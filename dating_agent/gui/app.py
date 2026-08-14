#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio 界面 - 4个Tab
Tab 1: 我的档案 (手动填/蒸馏生成)
Tab 2: 筛选 (粘贴对方profile看评分)
Tab 3: 聊天 (接API跟匹配对象聊)
Tab 4: 报告 (查看评估结果)
"""

import json
import os
import gradio as gr

from ..profile import PersonalityProfile
from ..llm_client import LLMClient, LLMConfig
from ..filter_engine import FilterEngine
from ..chat_engine import ChatEngine
from ..distill import Distiller
from ..agent import DatingAgent


# ─── 全局状态 ───
_state = {
    "profile": None,
    "llm": None,
    "agent": None,
    "matches": [],
    "shortlisted": [],
    "chat_histories": {},  # match_id -> [{"role","content"}]
    "current_match_id": None,
}


def _get_llm(api_key, base_url, model):
    if not api_key:
        return None
    config = LLMConfig(api_key=api_key, base_url=base_url or "https://api.deepseek.com/v1",
                       model=model or "deepseek-chat")
    return LLMClient(config)


# ─── Tab 1: 我的档案 ───

def save_profile(name, gender, age, personality_tags, likes, dislikes, chat_style,
                 api_key, base_url, model):
    """保存手动填写的档案 + 初始化LLM"""
    tags = [t.strip() for t in personality_tags.split(",") if t.strip()]
    like_list = [l.strip() for l in likes.split(",") if l.strip()]
    dislike_list = [d.strip() for d in dislikes.split(",") if d.strip()]

    profile = PersonalityProfile(
        name=name or "匿名用户",
        gender=gender or "",
        age=int(age) if age else 0,
        personality_tags=tags or ["待填写"],
        likes=like_list or ["待填写"],
        dislikes=dislike_list or ["待填写"],
        chat_style=chat_style or "",
    )
    _state["profile"] = profile
    _state["llm"] = _get_llm(api_key, base_url, model)

    info = f"✅ 档案已保存: {profile.name}\n"
    info += f"   性格标签: {', '.join(profile.personality_tags)}\n"
    info += f"   喜欢: {', '.join(profile.likes)}\n"
    info += f"   讨厌: {', '.join(profile.dislikes)}\n"
    info += f"   LLM: {'已连接' if _state['llm'] else '未连接(规则模式)'}"
    return info


def distill_profile(chat_logs_text, name, gender, age, api_key, base_url, model):
    """从聊天记录蒸馏性格档案"""
    if not api_key:
        return "❌ 蒸馏需要LLM API Key，请先填写"

    try:
        lines = chat_logs_text.strip().split("\n")
        chat_logs = []
        for line in lines:
            if ":" in line:
                role, content = line.split(":", 1)
                role = "me" if role.strip().lower() in ("我", "me", "i") else "them"
                chat_logs.append({"role": role, "content": content.strip()})
    except Exception:
        return "❌ 聊天记录格式错误，每行格式: 我:xxx 或 对方:xxx"

    if len(chat_logs) < 5:
        return "❌ 聊天记录太少，至少需要5条"

    llm = _get_llm(api_key, base_url, model)
    if not llm:
        return "❌ LLM初始化失败"

    basic_info = {"name": name or "蒸馏用户", "gender": gender or "", "age": int(age) if age else 0}
    distiller = Distiller(llm)
    profile = distiller.distill(chat_logs, basic_info)
    _state["profile"] = profile
    _state["llm"] = llm

    result = f"✅ 蒸馏完成!\n"
    result += f"   姓名: {profile.name}\n"
    result += f"   性格标签: {', '.join(profile.personality_tags)}\n"
    result += f"   喜欢: {', '.join(profile.likes)}\n"
    result += f"   讨厌: {', '.join(profile.dislikes)}\n"
    result += f"   聊天风格: {profile.chat_style[:100]}..."
    return result


# ─── Tab 2: 筛选 ───

def evaluate_one(bio, interests, photo_desc):
    """评估单个profile"""
    if not _state["profile"]:
        return "❌ 请先在Tab 1保存档案"

    interest_list = [i.strip() for i in interests.split(",") if i.strip()]
    engine = FilterEngine(_state["profile"], _state["llm"])
    result = engine.evaluate(bio or "", interest_list, photo_desc or "")

    verdict = "✅ 右滑" if result["should_swipe_right"] else "❌ 左滑"
    output = f"{verdict} (评分: {result['score']}/100)\n原因: {result['reason']}"
    return output


def batch_swipe(profiles_json):
    """批量筛选"""
    if not _state["profile"]:
        return "❌ 请先在Tab 1保存档案"

    try:
        profiles = json.loads(profiles_json)
    except json.JSONDecodeError:
        return "❌ JSON格式错误，请输入有效的profile列表"

    agent = DatingAgent(_state["profile"], _state["llm"])
    matches = agent.swipe(profiles, verbose=False)
    # P1修复: 给每个match写入id字段，供聊天Tab使用
    for i, m in enumerate(matches):
        if "id" not in m:
            m["id"] = str(i + 1)
    _state["agent"] = agent
    _state["matches"] = matches

    output = f"📊 筛选结果: {len(profiles)}人 -> 右滑 {len(matches)}人\n\n"
    for i, m in enumerate(matches):
        output += f"{i+1}. {m.get('name', '匿名')} - {m.get('bio', '')[:50]}...\n"
    return output


# ─── Tab 3: 聊天 ───

def start_chat(match_index):
    """选择一个匹配对象开始聊天"""
    if not _state["matches"]:
        return "❌ 没有匹配对象，请先在Tab 2筛选", ""

    try:
        idx = int(match_index) - 1
        match = _state["matches"][idx]
    except (ValueError, IndexError):
        return "❌ 无效序号", ""

    match_id = str(match.get("id", match.get("name", "default")))
    _state["current_match_id"] = match_id

    if not _state["llm"]:
        return "❌ 聊天需要LLM API，请在Tab 1配置", ""

    if match_id not in _state["chat_histories"]:
        _state["chat_histories"][match_id] = []

    engine = ChatEngine(_state["profile"], _state["llm"])
    opener = engine.start_conversation(match_id)
    _state["chat_histories"][match_id].append({"role": "me", "content": opener})

    history_text = _format_chat(match_id)
    return f"💬 已开始与 {match.get('name', '匿名')} 聊天\nAI发了第一条: {opener}", history_text


def send_message(message):
    """发送消息并获取AI回复"""
    match_id = _state["current_match_id"]
    if not match_id:
        return "❌ 请先选择聊天对象", ""

    if not message.strip():
        return "请输入消息", _format_chat(match_id)

    # 记录对方消息
    _state["chat_histories"][match_id].append({"role": "them", "content": message})

    # AI回复
    engine = ChatEngine(_state["profile"], _state["llm"])
    # 恢复历史
    engine.conversations[match_id] = _state["chat_histories"][match_id]
    reply = engine.reply(match_id, message)
    _state["chat_histories"][match_id].append({"role": "me", "content": reply})

    return "", _format_chat(match_id)


def evaluate_chat():
    """评估当前对话"""
    match_id = _state["current_match_id"]
    if not match_id:
        return "❌ 没有活跃的对话"

    engine = ChatEngine(_state["profile"], _state["llm"])
    engine.conversations[match_id] = _state["chat_histories"][match_id]
    result = engine.evaluate(match_id)

    verdict = ""
    if result.get("should_meet"):
        verdict = "⭐ 推荐见面!"
        # P1修复: 评估结果同步到_state
        match = _get_current_match()
        if match:
            match["eval_score"] = result["score"]
            match["eval_reason"] = result["reason"]
            if match not in _state["shortlisted"]:
                _state["shortlisted"].append(match)
    elif result.get("should_drop"):
        verdict = "💤 建议放弃"
    else:
        verdict = "🤔 可以再聊聊"

    return f"{verdict} (评分: {result['score']}/100)\n{result['reason']}"


def _get_current_match():
    """获取当前聊天的match对象"""
    match_id = _state.get("current_match_id")
    if not match_id:
        return None
    for m in _state.get("matches", []):
        if str(m.get("id", m.get("name", ""))) == match_id:
            return m
    return None


def _format_chat(match_id):
    """格式化聊天记录"""
    history = _state["chat_histories"].get(match_id, [])
    lines = []
    for msg in history:
        prefix = "🤖 你" if msg["role"] == "me" else "👤 对方"
        lines.append(f"{prefix}: {msg['content']}")
    return "\n\n".join(lines) if lines else "暂无消息"


# ─── Tab 4: 报告 ───

def generate_report():
    """生成运行报告"""
    if not _state["agent"]:
        return "❌ 没有运行记录，请先筛选和聊天"

    agent = _state["agent"]
    # P1修复: 同步聊天评估结果到agent
    agent.shortlisted = _state.get("shortlisted", [])
    agent.matches = _state.get("matches", [])
    report = agent.report()
    return json.dumps(report, ensure_ascii=False, indent=2)


def save_results(filepath):
    """保存结果"""
    if not _state["agent"]:
        return "❌ 没有可保存的结果"
    filepath = filepath or "dating_results.json"
    _state["agent"].save_results(filepath)
    return f"✅ 结果已保存到 {filepath}"


# ─── 构建界面 ───

def create_app():
    """创建Gradio界面"""
    with gr.Blocks(title="AI相亲Agent", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🎯 AI相亲Agent")
        gr.Markdown("蒸馏自己，替你初筛。AI帮你刷交友软件，聊得来的推给你真人接管。")

        # ─── Tab 1: 我的档案 ───
        with gr.Tab("📋 我的档案"):
            gr.Markdown("### 手动填写档案")
            with gr.Row():
                name_input = gr.Textbox(label="姓名", value="")
                gender_input = gr.Textbox(label="性别", value="")
                age_input = gr.Number(label="年龄", value=0)
            with gr.Row():
                tags_input = gr.Textbox(label="性格标签(逗号分隔)", placeholder="内向,爱看书,幽默")
                likes_input = gr.Textbox(label="喜欢什么特质(逗号分隔)", placeholder="有责任心,爱运动")
                dislikes_input = gr.Textbox(label="讨厌什么特质(逗号分隔)", placeholder="抽烟,酗酒")
            chat_style_input = gr.Textbox(label="聊天风格描述", placeholder="直接、不绕弯、偶尔幽默",
                                          lines=2)

            gr.Markdown("### LLM配置 (聊天和蒸馏必填)")
            with gr.Row():
                api_key_input = gr.Textbox(label="API Key", type="password", placeholder="sk-xxx")
                base_url_input = gr.Textbox(label="Base URL", value="https://api.deepseek.com/v1")
                model_input = gr.Textbox(label="模型", value="deepseek-chat")

            save_btn = gr.Button("💾 保存档案", variant="primary")
            save_output = gr.Textbox(label="状态", lines=5)

            save_btn.click(
                fn=save_profile,
                inputs=[name_input, gender_input, age_input, tags_input,
                        likes_input, dislikes_input, chat_style_input,
                        api_key_input, base_url_input, model_input],
                outputs=save_output,
            )

            gr.Markdown("---\n### 或者：从聊天记录蒸馏")
            chat_logs_input = gr.Textbox(
                label="聊天记录 (每行格式: 我:xxx 或 对方:xxx)",
                lines=10,
                placeholder="我:你好呀\n对方:你好\n我:平时喜欢干什么\n对方:看书健身\n...",
            )
            distill_btn = gr.Button("🧪 蒸馏档案", variant="secondary")
            distill_output = gr.Textbox(label="蒸馏结果", lines=6)

            distill_btn.click(
                fn=distill_profile,
                inputs=[chat_logs_input, name_input, gender_input, age_input,
                        api_key_input, base_url_input, model_input],
                outputs=distill_output,
            )

        # ─── Tab 2: 筛选 ───
        with gr.Tab("🔍 筛选"):
            gr.Markdown("### 评估单个Profile")
            with gr.Row():
                bio_input = gr.Textbox(label="对方Bio", lines=3, placeholder="对方自我介绍...")
                interests_input = gr.Textbox(label="对方兴趣(逗号分隔)", placeholder="电影,旅行,美食")
            photo_desc_input = gr.Textbox(label="照片描述(可选)", placeholder="穿白T恤，笑容阳光")

            eval_btn = gr.Button("🔍 评估", variant="primary")
            eval_output = gr.Textbox(label="评估结果", lines=3)
            eval_btn.click(fn=evaluate_one,
                           inputs=[bio_input, interests_input, photo_desc_input],
                           outputs=eval_output)

            gr.Markdown("---\n### 批量筛选 (JSON格式)")
            batch_input = gr.Textbox(
                label="Profile列表JSON",
                lines=10,
                placeholder='[{"id":"1","name":"小A","bio":"...","interests":["..."]}]',
            )
            batch_btn = gr.Button("🔍 批量筛选", variant="primary")
            batch_output = gr.Textbox(label="筛选结果", lines=10)
            batch_btn.click(fn=batch_swipe, inputs=batch_input, outputs=batch_output)

        # ─── Tab 3: 聊天 ───
        with gr.Tab("💬 聊天"):
            gr.Markdown("### 选择匹配对象聊天")
            match_index_input = gr.Number(label="匹配序号(从筛选结果中选)", value=1, precision=0)
            start_btn = gr.Button("🚀 开始聊天", variant="primary")
            start_output = gr.Textbox(label="状态", lines=2)

            gr.Markdown("---\n### 对话")
            chat_display = gr.Textbox(label="聊天记录", lines=15, interactive=False)
            msg_input = gr.Textbox(label="输入对方的消息(模拟对方回复)", placeholder="对方说: ...")
            send_btn = gr.Button("📤 发送", variant="primary")

            send_btn.click(fn=send_message, inputs=msg_input,
                           outputs=[msg_input, chat_display])

            start_btn.click(fn=start_chat, inputs=match_index_input,
                            outputs=[start_output, chat_display])

            gr.Markdown("---\n### 评估对话")
            eval_chat_btn = gr.Button("📊 评估当前对话", variant="secondary")
            eval_chat_output = gr.Textbox(label="评估结果", lines=3)
            eval_chat_btn.click(fn=evaluate_chat, outputs=eval_chat_output)

        # ─── Tab 4: 报告 ───
        with gr.Tab("📊 报告"):
            gr.Markdown("### 运行报告")
            report_btn = gr.Button("📋 生成报告", variant="primary")
            report_output = gr.Textbox(label="报告", lines=15)
            report_btn.click(fn=generate_report, outputs=report_output)

            gr.Markdown("---\n### 保存结果")
            filepath_input = gr.Textbox(label="保存路径", value="dating_results.json")
            save_btn2 = gr.Button("💾 保存", variant="secondary")
            save_output2 = gr.Textbox(label="状态", lines=2)
            save_btn2.click(fn=save_results, inputs=filepath_input, outputs=save_output2)

    return app
