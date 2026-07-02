import os
import re
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd
import streamlit as st
from openai import OpenAI


# =========================
# 1. 基础配置
# =========================

st.set_page_config(
    page_title="慢慢说：校园社交场景预演智能体",
    page_icon="🌷",
    layout="wide"
)


def apply_soft_theme():
    st.markdown("""
    <style>
    /* 整体字体：圆润、清晰、低刺激 */
    html, body, [class*="css"], .stApp {
        font-family:
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "PingFang SC",
            "Noto Sans SC",
            "YouYuan",
            "Comic Sans MS",
            sans-serif !important;
        font-size: 16px;
        line-height: 1.75;
        color: #4F4A5A;
    }

    /* 页面背景：奶油色 + 淡粉紫，避免刺眼 */
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 213, 230, 0.36), transparent 28%),
            radial-gradient(circle at top right, rgba(196, 232, 255, 0.34), transparent 30%),
            linear-gradient(180deg, #FFFDF8 0%, #FFF7FC 55%, #F7FBFF 100%);
    }

    /* 左侧栏：柔和粉白 */
    section[data-testid="stSidebar"] {
        background: #FFF7FB !important;
        border-right: 1px solid #F2DFEA;
    }

    section[data-testid="stSidebar"] * {
        font-family:
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "PingFang SC",
            "YouYuan",
            sans-serif !important;
    }

    /* 标题：圆润一点，不要太硬 */
    h1 {
        color: #5E5A7A !important;
        font-size: 34px !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }

    h2, h3 {
        color: #625F7D !important;
        font-weight: 750 !important;
    }

    /* 普通说明文字 */
    .stCaption, .small-note, p {
        color: #6F6A7D;
        line-height: 1.8;
    }

    /* 可爱卡片 */
    .cute-card {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid #F3E3ED;
        border-radius: 24px;
        padding: 18px 20px;
        box-shadow: 0 8px 22px rgba(110, 88, 120, 0.06);
        margin-bottom: 14px;
    }

    /* 步骤提示框 */
    .step-box {
        background: #F8FBFF;
        border: 1px solid #DCEFFD;
        border-radius: 22px;
        padding: 16px 18px;
        margin: 14px 0;
        color: #536174;
    }

    /* 当前角色/场景卡片 */
    .role-box {
        background: #FFF9ED;
        border: 1px solid #F6E3B7;
        border-radius: 22px;
        padding: 16px 18px;
        margin: 14px 0;
        color: #5E5543;
    }

    /* 反馈卡片 */
    .feedback-box {
        background: #F4FFF6;
        border: 1px solid #CFEFD5;
        border-radius: 22px;
        padding: 16px 18px;
        margin: 14px 0;
        color: #4D6653;
    }

    /* 小标签 */
    .cute-tag {
        display: inline-block;
        background: #FCEEF5;
        color: #7D5A72;
        border-radius: 999px;
        padding: 5px 13px;
        font-size: 14px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 8px;
    }

    /* 按钮：圆圆的，像软糖，但不刺眼 */
    .stButton > button {
        background: linear-gradient(90deg, #BFE6F8 0%, #F8CDE2 100%) !important;
        color: #4E4A5D !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.65rem 1.25rem !important;
        font-weight: 700 !important;
        box-shadow: 0 5px 14px rgba(120, 100, 140, 0.10);
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #AEDDF4 0%, #F5BED9 100%) !important;
        color: #3F3B4E !important;
        transform: translateY(-1px);
    }

    /* 输入框、选择框：圆角、宽松 */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"],
    .stMultiSelect div[data-baseweb="select"] {
        border-radius: 18px !important;
        border-color: #EADDE8 !important;
        background: #FFFFFF !important;
        font-size: 16px !important;
    }

    /* 聊天气泡 — 去掉统一背景，由 inline 控制左右区分 */
    div[data-testid="stChatMessage"] {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 4px 8px;
        margin-bottom: 8px;
        box-shadow: none;
    }

    /* AI 聊天气泡：靠左，暖白底 */
    .chat-bubble-ai {
        display: inline-block;
        max-width: 78%;
        background: #FFFAF5;
        border: 1px solid #F3E8DF;
        border-radius: 6px 20px 20px 20px;
        padding: 14px 18px;
        color: #4F4A5A;
        line-height: 1.75;
        box-shadow: 0 3px 10px rgba(100, 80, 120, 0.04);
    }

    /* 用户聊天气泡：靠右，淡蓝底 */
    .chat-bubble-user {
        display: inline-block;
        max-width: 78%;
        background: #F3F8FF;
        border: 1px solid #DCE8F5;
        border-radius: 20px 6px 20px 20px;
        padding: 14px 18px;
        color: #4F4A5A;
        line-height: 1.75;
        box-shadow: 0 3px 10px rgba(100, 120, 160, 0.04);
        float: right;
    }

    .chat-meta {
        font-size: 13px;
        color: #8C8799;
        margin-bottom: 6px;
    }

    /* 指标卡片 */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #EFE5F0;
        border-radius: 22px;
        padding: 12px 14px;
        box-shadow: 0 5px 14px rgba(100, 80, 120, 0.04);
    }

    /* 展开框 */
    details {
        background: rgba(255, 255, 255, 0.75);
        border-radius: 18px !important;
        border: 1px solid #F0E5EF !important;
    }

    /* 减少页面压迫感 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1120px;
    }

    /* 顶部 Hero 区块 */
    .hero-wrap {
        width: 100%;
        display: flex;
        justify-content: center;
        margin-top: 6px;
        margin-bottom: 24px;
    }

    .hero-card {
        width: 100%;
        max-width: 1080px;
        text-align: center;
        background: linear-gradient(90deg, rgba(255,248,252,0.95) 0%, rgba(248,250,255,0.95) 100%);
        border: 1px solid #EFE6F2;
        border-radius: 30px;
        padding: 34px 28px 30px 28px;
        box-shadow: 0 10px 28px rgba(120, 95, 140, 0.06);
    }

    .hero-badge {
        display: inline-block;
        background: #FFF0F7;
        color: #8E6A86;
        border: 1px solid #F5DCEB;
        border-radius: 999px;
        padding: 6px 16px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 14px;
    }

    .hero-title {
        font-size: 48px;
        font-weight: 800;
        color: #666184;
        letter-spacing: 0.5px;
        line-height: 1.25;
        margin-bottom: 14px;
    }

    .hero-subtitle {
        max-width: 760px;
        margin: 0 auto;
        font-size: 22px;
        color: #8C8799;
        line-height: 1.85;
    }

    /* 小屏幕适配 */
    @media (max-width: 900px) {
        .hero-card {
            padding: 26px 18px 22px 18px;
            border-radius: 24px;
        }

        .hero-title {
            font-size: 34px;
        }

        .hero-subtitle {
            font-size: 18px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def get_secret(key: str, default: str = "") -> str:
    """同时兼容本地环境变量和 Streamlit secrets。"""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


API_KEY = get_secret("DASHSCOPE_API_KEY")
MODEL_NAME = get_secret("QWEN_MODEL", "qwen3.7-plus")
BASE_URL = get_secret(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)

DATA_PATH = Path("realistic_school_roleplay_asd_5000.csv")


def get_client() -> OpenAI:
    if not API_KEY:
        st.error("没有检测到 DASHSCOPE_API_KEY。请先在 .streamlit/secrets.toml 中配置 API Key。")
        st.stop()
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


# =========================
# 2. 读取数据集
# =========================

@st.cache_data
def load_roleplay_dataset(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()

    df = pd.read_csv(p)
    df = df.fillna("")
    return df


def get_unique_options(df: pd.DataFrame, col: str) -> List[str]:
    if df.empty or col not in df.columns:
        return []
    values = [str(x) for x in df[col].dropna().unique().tolist() if str(x).strip()]
    return sorted(values)


# 训练重点映射：后台细分类别 → 前台 4 大类
TRAINING_FOCUS_MAP = {
    "开始对话": [
        "打招呼", "加入对话", "主动开口", "问候老师", "问候同学",
        "开场回应", "加入聊天", "开始对话", "发起对话", "社交开场",
        "问候", "自我介绍", "破冰",
    ],
    "回应别人": [
        "接话", "回应邀请", "回应提醒", "回应别人", "回应问题",
        "回答提问", "回应意见", "表达意见", "回应同学", "回应老师",
        "回应赞美", "回应批评", "回应玩笑", "日常应答",
    ],
    "请求帮助": [
        "求助", "提问", "请求澄清", "请求帮助", "听不懂",
        "不会做", "找不到", "需要帮忙", "请求重复", "请求解释",
        "寻求支持", "问路", "请教问题",
    ],
    "表达拒绝或不舒服": [
        "拒绝", "表达不舒服", "表达不同意见", "不想参加", "不喜欢",
        "感到紧张", "想换座位", "想休息", "结束对话", "情绪表达",
        "压力倾诉", "座位调整", "表达边界", "说不",
    ],
}


def map_training_focus(broad_category: str) -> List[str]:
    if broad_category == "不限":
        return []
    return TRAINING_FOCUS_MAP.get(broad_category, [])


# 校园环境：合并为常见分类
ENVIRONMENT_OPTIONS = [
    "教室/课堂", "课间/走廊", "食堂/操场",
    "图书馆/自习", "老师办公室", "小组/班级活动",
]
ENVIRONMENT_MAP = {
    "教室/课堂":      ["教室", "课堂", "上课", "课堂上"],
    "课间/走廊":      ["课间", "走廊", "楼道", "下课"],
    "食堂/操场":      ["食堂", "操场", "餐厅", "体育课", "运动场"],
    "图书馆/自习":    ["图书馆", "自习", "自习室", "阅览室"],
    "老师办公室":     ["老师办公室", "办公室", "教师办公室", "辅导员办公室"],
    "小组/班级活动":  ["小组", "班级活动", "班队活动", "社团", "活动室", "班会"],
}


def map_environment(broad_env: str) -> List[str]:
    if broad_env == "不限":
        return []
    return ENVIRONMENT_MAP.get(broad_env, [broad_env])


def filter_dataset(
    df: pd.DataFrame,
    stage: str,
    interaction_type: str,
    environment: str,
    training_focus: str
) -> pd.DataFrame:
    result = df.copy()
    if stage != "不限":
        result = result[result["stage"] == stage]
    if interaction_type != "不限":
        result = result[result["interaction_type"] == interaction_type]
    if environment != "不限":
        mapped_envs = map_environment(environment)
        if mapped_envs:
            result = result[result["environment"].isin(mapped_envs)]
    if training_focus != "不限":
        mapped_values = map_training_focus(training_focus)
        if mapped_values:
            result = result[result["training_focus"].isin(mapped_values)]
    return result


def select_case(filtered_df: pd.DataFrame) -> Dict[str, Any]:
    if filtered_df.empty:
        return {}
    row = filtered_df.sample(1, random_state=random.randint(1, 999999)).iloc[0]
    return row.to_dict()


# =========================
# 3. 隐私脱敏与安全边界
# =========================

PRIVACY_PATTERNS = [
    ("手机号", r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    ("邮箱", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("身份证号", r"(?<!\d)\d{17}[\dXx](?!\d)"),
    ("QQ号", r"(QQ|qq)[:：\s]*\d{5,12}"),
    ("微信号", r"(微信|vx|VX|wechat)[:：\s]*[A-Za-z0-9_-]{5,20}"),
    ("学校/机构", r"[一-龥]{2,30}(大学|学院|中学|小学|公司|集团|医院|实验室)"),
    ("地址", r"[一-龥]{2,20}(省|市|区|县|镇|街道|小区|公寓|花园|大厦|广场|路|街|巷|栋|单元)")
]


def mask_privacy(text: str) -> Tuple[str, List[Dict[str, str]]]:
    masked_text = text
    found_items = []

    for label, pattern in PRIVACY_PATTERNS:
        for m in re.finditer(pattern, masked_text):
            original = m.group(0)
            if "[" in original or "]" in original:
                continue
            found_items.append({"type": label, "value": original})
        masked_text = re.sub(pattern, f"[{label}]", masked_text)

    name_pattern = r"(我叫|我是|本人叫)([一-龥]{2,4})"
    for m in re.finditer(name_pattern, masked_text):
        found_items.append({"type": "姓名", "value": m.group(2)})
    masked_text = re.sub(name_pattern, r"\1[姓名]", masked_text)

    return masked_text, found_items


CRISIS_KEYWORDS = [
    "不想活", "想死", "自杀", "轻生", "结束生命", "活不下去",
    "伤害自己", "割腕", "跳楼", "服药", "再也不想醒来"
]


def local_crisis_check(text: str) -> bool:
    return any(keyword in text for keyword in CRISIS_KEYWORDS)


# =========================
# 领域边界判断
# =========================

OUT_OF_SCOPE_KEYWORDS = [
    "股票", "基金", "投资", "理财", "炒股", "比特币", "币圈", "预测股价",
    "星盘", "八字", "塔罗", "算命", "占卜",
    "减肥药", "药物", "诊断", "疾病治疗",
    "代写论文", "代写作业", "作业答案", "帮我写完整论文",
    "帮我写代码", "代码报错", "debug", "程序报错",
]


def is_out_of_scope(user_text: str) -> bool:
    """判断是否明显偏离校园社交/校园学习交流。数学、作业、讲题、请教老师不算越界。"""
    text = user_text.strip()
    return any(keyword in text for keyword in OUT_OF_SCOPE_KEYWORDS)


def build_boundary_reply(user_text: str, case: Dict[str, Any]) -> str:
    if "股票" in user_text or "投资" in user_text or "基金" in user_text:
        example = "老师，我最近对股票分析感兴趣，可以推荐一些适合入门的学习资料吗？"
    elif "代码" in user_text or "编程" in user_text:
        example = "同学，我这段代码有点看不懂，你方便帮我看一下思路吗？"
    elif "论文" in user_text or "作业" in user_text:
        example = "老师，我这个作业不知道从哪里开始，可以请您给我一点提示吗？"
    else:
        example = "老师/同学，我有一个问题想请教你，可以吗？"

    return f"""
这个问题不太属于我主要练习的内容。🌷

我主要是陪你练习校园里的真实交流，比如和同学说话、向老师提问、表达拒绝、请求帮助、加入对话等。

我们可以把这个问题变成一个校园沟通练习。
你可以试着这样说：

**「{example}」**

你也可以只回我一句：「我想练习怎么问老师。」我会继续陪你练。
""".strip()


# ── 用户主动换话题检测 ──

USER_TOPIC_SHIFT_PATTERNS = [
    "我想", "我要", "我不想", "我现在", "我有点", "我觉得",
    "等一下", "先不", "先别", "可以不", "我想去", "我要去",
    "我想要", "我需要", "我不舒服", "我累了", "我饿了",
]


def is_user_topic_shift(user_text: str) -> bool:
    """判断用户是否主动提出了新的需求、感受或话题。"""
    text = user_text.strip()
    return any(text.startswith(pattern) for pattern in USER_TOPIC_SHIFT_PATTERNS)


# ── 聊天历史格式化 ──

def format_chat_history(history, max_messages: int = 8) -> str:
    """整理最近几轮对话，避免模型每轮都像重新开始。"""
    if not history:
        return "暂无历史对话。"
    recent = history[-max_messages:]
    lines = []
    for msg in recent:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"学习者：{content}")
        elif role == "assistant":
            lines.append(f"AI角色：{content}")
    return "\n".join(lines)


# =========================
# 学段适配判断
# =========================

STAGE_ORDER = {
    "小学阶段": 1,
    "中学阶段": 2,
    "大学阶段": 3,
}

# ── 校园学习交流判断 ──

SCHOOL_STUDY_CONTEXT_KEYWORDS = [
    "不会", "不懂", "不明白", "没听懂", "跟不上", "看不懂", "不清楚",
    "讲一下", "讲解", "解释一下", "解释", "帮我看看", "帮我理一下",
    "请教", "问老师", "问同学", "同学帮我", "老师讲", "老师说",
    "题目", "作业", "课堂", "考试", "小测", "讲题", "展示",
    "小组讨论", "复习", "预习", "报告", "PPT",
    "方程", "函数", "二元一次方程", "一元一次方程",
    "数学", "物理", "化学", "英语", "作文", "语文",
    "微积分", "复变函数", "高数", "线性代数", "概率论",
]


def is_school_study_communication(user_text: str) -> bool:
    """判断是否属于校园学习交流。这类内容不应该被边界拦截。"""
    text = user_text.strip()
    return any(keyword in text for keyword in SCHOOL_STUDY_CONTEXT_KEYWORDS)


# ── 完整答题检测 ──

FULL_ACADEMIC_ANSWER_KEYWORDS = [
    "帮我解", "直接解", "答案是什么", "完整答案", "标准答案",
    "帮我算", "证明过程", "完整证明", "详细推导",
]


def is_full_academic_answer_request(user_text: str) -> bool:
    return any(keyword in user_text for keyword in FULL_ACADEMIC_ANSWER_KEYWORDS)


# ── 知识点-学段映射 ──

ACADEMIC_TOPIC_LEVELS = {
    "加减法": "小学阶段", "乘法": "小学阶段",
    "除法": "小学阶段", "分数": "小学阶段", "小数": "小学阶段",
    "一元一次方程": "中学阶段", "二元一次方程": "中学阶段",
    "方程": "中学阶段", "函数": "中学阶段",
    "物理实验": "中学阶段", "化学实验": "中学阶段",
    "微积分": "大学阶段", "高数": "大学阶段",
    "线性代数": "大学阶段", "概率论": "大学阶段",
    "复变函数": "大学阶段",
}


def detect_academic_topic(user_text: str):
    for topic, required_stage in ACADEMIC_TOPIC_LEVELS.items():
        if topic in user_text:
            return topic, required_stage
    return None, None


def stage_can_understand(current_stage: str, required_stage: str) -> bool:
    current_level = STAGE_ORDER.get(current_stage, 1)
    required_level = STAGE_ORDER.get(required_stage, 3)
    return current_level >= required_level


# ── 角色与意图判断 ──

EXPLAIN_INTENT_KEYWORDS = [
    "讲解", "解释", "讲一下", "解释一下", "重点", "不清楚",
    "不明白", "没听懂", "帮我讲", "给我讲", "能不能讲",
]


def is_explain_request(user_text: str) -> bool:
    return any(keyword in user_text for keyword in EXPLAIN_INTENT_KEYWORDS)


def is_teacher_role(case: Dict[str, Any]) -> bool:
    role_text = str(case.get("ai_role", "")) + str(case.get("interaction_type", ""))
    return "老师" in role_text


def is_peer_role(case: Dict[str, Any]) -> bool:
    role_text = str(case.get("ai_role", "")) + str(case.get("interaction_type", ""))
    return any(word in role_text for word in ["同学", "组员", "室友", "队友"])


def build_study_communication_reply(user_text: str, case: Dict[str, Any]) -> str:
    """处理校园学习交流类输入。根据老师/同学角色调整语气，允许简短知识讲解。"""
    current_stage = case.get("stage", "中学阶段")

    topic, required_stage = detect_academic_topic(user_text)

    if topic:
        st.session_state.last_academic_topic = topic
    elif is_explain_request(user_text):
        topic = st.session_state.get("last_academic_topic", None)

    # 不能直接完整代做
    if is_full_academic_answer_request(user_text):
        if is_teacher_role(case):
            return """
可以，我可以帮你理清思路，但不会直接替你完成整道题。🌷

你先告诉我：你现在卡在哪一步？
是看不懂题目条件，还是不知道怎么列式，或者是不知道怎么继续计算？

你可以这样问：

**「老师，我这一步不知道为什么要这样做，可以请您提示一下吗？」**
""".strip()
        else:
            return """
可以，我可以陪你一起看思路，但我不直接把完整答案写完。🌷

你可以先告诉我你做到哪一步了，我帮你看看哪里卡住了。

你也可以这样说：

**「同学，我这道题卡在第一步了，你能不能帮我讲一下思路？」**
""".strip()

    # 微积分
    if topic == "微积分" or "微积分" in user_text or topic == "高数":
        if current_stage in ("小学阶段", "中学阶段"):
            return """
微积分一般是更高年级，尤其是大学阶段会系统学习的内容。🌷

简单来说，它主要研究两个问题：

1. **变化**：一个量变化得有多快，比如速度怎么变化；
2. **积累**：很多很小的部分加起来，最后变成一个整体。

你现在不用完全弄懂，可以先把它理解成：
**微积分是研究变化和积累的数学工具。**

你可以问老师：

**「老师，微积分是不是以后才会学？它大概是研究什么的呀？」**
""".strip()

        if is_teacher_role(case):
            return """
可以。微积分的重点可以先抓住三个词：**极限、导数、积分**。🌷

**第一，极限是基础。**
它研究的是一个量不断接近某个值时，会趋向什么结果。

**第二，导数看「变化率」。**
比如速度就是位置变化的快慢，导数就是用来描述「变化有多快」。

**第三，积分看「累积量」。**
它可以理解为把很多很小的部分加起来，得到一个整体。

你可以先记住一句话：

**导数关注变化，积分关注累积，极限是理解它们的基础。**

你现在最不清楚的是导数，还是积分？
""".strip()

        return """
可以呀，我给你讲个大概。🌷

微积分最核心的其实就是两个东西：**变化**和**累积**。

**导数**就是看一个东西变化得有多快。
比如速度，其实就是位置对时间的变化率。

**积分**就是把很多小部分加起来。
比如把很多很窄的小面积加起来，就能得到一个整体面积。

所以你可以先这样理解：

**导数是在问「变得多快」，积分是在问「加起来有多少」。**

你是卡在导数，还是积分那里？
""".strip()

    # 复变函数
    if topic == "复变函数" or "复变函数" in user_text:
        if current_stage in ("小学阶段", "中学阶段"):
            return """
复变函数一般是大学数学里比较高阶的内容，我们现在这个阶段通常还不会系统学习。🌷

简单说，它和「复数里的函数」有关，会比普通函数更抽象一些。

你可以这样问老师：

**「老师，复变函数是不是大学才会学？它和我们现在学的函数有什么关系呀？」**
""".strip()

        if is_teacher_role(case):
            return """
可以简单说一下。复变函数是研究「复数范围内的函数」的课程。🌷

你可以先这样理解：

我们以前学的函数大多是在实数范围内讨论，比如 x 和 y 是普通实数。
复变函数则把变量扩展到复数范围，比如 z = a + bi。

它通常会涉及复数、解析函数、积分等内容，比普通函数更抽象。

不过现在先不用急着深入，你可以先抓住一句话：

**复变函数就是研究复数范围内函数性质的数学内容。**
""".strip()

        return """
复变函数我大概知道一点，它一般是大学里比较高阶的数学课。🌷

简单说，就是把普通函数放到复数范围里研究。

你可以先这样问老师：

**「老师，复变函数和我们之前学的函数有什么区别？」**
""".strip()

    # 二元一次方程/方程
    if topic in ("二元一次方程", "一元一次方程", "方程") or "方程" in user_text:
        if current_stage == "小学阶段":
            return """
方程可能是高一点年级会系统学的内容。🌷

你可以先简单理解成：
**用一个未知数表示不知道的数，再根据题目里的关系把它找出来。**

你可以问老师：

**「老师，这个方程我现在还不太懂，可以先告诉我第一步要看什么吗？」**
""".strip()

        if is_teacher_role(case):
            return """
可以。以二元一次方程为例，重点是这几个步骤：🌷

1. **找未知数**：题目里有两个不知道的量，就可以设成 x 和 y；
2. **列两个方程**：根据题目给出的两个条件，分别列出方程；
3. **选择方法求解**：常用方法是代入法或加减法；
4. **检查答案**：把求出的 x、y 代回题目，看是否符合条件。

你可以先记住一句话：

**二元一次方程的关键是：设两个未知数，列两个关系式，再消去一个未知数。**

你现在是不清楚「怎么列方程」，还是不清楚「怎么消元」？
""".strip()

        return """
可以呀，二元一次方程我们可以一起理一下。🌷

它一般就是有两个未知数，比如 x 和 y。常见思路是：

1. 先把两个不知道的量设成 x 和 y；
2. 根据题目条件列出两个方程；
3. 用代入法或者加减法，先求出一个未知数；
4. 再把它代回去求另一个未知数。

如果你等下要展示，可以先这样说：

**「我先设两个未知数，然后根据题目条件列出两个方程，接着用消元的方法求解。」**

你可以把你准备讲的第一句话发给我，我帮你看看顺不顺。
""".strip()

    # 其他已识别知识点
    if topic:
        if not stage_can_understand(current_stage, required_stage):
            return f"""
「{topic}」听起来有点超过我们现在的学习阶段，可能是更高年级或者大学才会系统学习的内容。🌷

不过可以简单理解为：它是一个更高级的知识点，现在不需要一下子完全弄懂。

如果你是想问老师，可以这样说：

**「老师，这个内容我现在还没学过，可以简单告诉我它大概是什么吗？」**
""".strip()

        if is_teacher_role(case):
            return f"""
可以。关于{topic}，我先讲一下最核心的部分。🌷

你可以先抓住它的基本思路，不用一次性全部弄懂。你现在具体是哪里不清楚？可以先告诉我你卡在哪一步，我再继续帮你理。
""".strip()

        return f"""
这个内容我们可以简单聊一下。🌷

{topic}和当前学习场景有关，你可以把它当成一次向同学或老师请教的练习。

你可以这样开口：

**「我对{topic}这个部分有点不明白，你方便给我讲一下思路吗？」**
""".strip()

    # 没识别到具体知识点，但属于学习交流
    if is_teacher_role(case):
        return """
可以。你先告诉我你具体不明白哪一部分。🌷

你可以这样说：

**「老师，我这个地方有点跟不上，主要是不清楚第一步为什么要这样做。」**

你可以把题目、知识点，或者你听不懂的那句话发给我。
""".strip()

    return """
可以呀，我们可以一起练。🌷

你可以先这样说：

**「我这个地方有点不懂，你能不能先给我讲一下思路？」**

或者：

**「我先试着讲一遍，你帮我听听哪里不清楚。」**

你把想问的问题，或者准备讲的第一句话发给我就可以。
""".strip()


# ── 角色知识询问检测 ──

ACADEMIC_TOPICS = [
    "微积分", "复变函数", "高数", "线性代数", "概率论",
    "导数", "函数", "方程", "物理", "化学", "英语",
    "加减法", "乘法", "除法", "分数", "离散数学",
]

ASK_KNOWLEDGE_PATTERNS = [
    "学过", "会不会", "懂不懂", "知道", "了解", "听说过",
    "你会", "你懂", "你知道", "你学过", "你了解",
]


def is_asking_role_knowledge(user_text: str) -> bool:
    has_topic = any(topic in user_text for topic in ACADEMIC_TOPICS)
    has_ask_pattern = any(pattern in user_text for pattern in ASK_KNOWLEDGE_PATTERNS)
    return has_topic and has_ask_pattern


def build_role_knowledge_reply(user_text: str, case: Dict[str, Any]) -> str:
    stage = case.get("stage", "中学阶段")
    ai_role = case.get("ai_role", "同学")

    if "复变函数" in user_text:
        topic = "复变函数"
    elif "微积分" in user_text:
        topic = "微积分"
    elif "线性代数" in user_text:
        topic = "线性代数"
    elif "概率论" in user_text:
        topic = "概率论"
    elif "离散数学" in user_text:
        topic = "离散数学"
    elif "高数" in user_text:
        topic = "高数"
    elif "导数" in user_text:
        topic = "导数"
    elif "函数" in user_text:
        topic = "函数"
    elif "方程" in user_text:
        topic = "方程"
    elif "物理" in user_text:
        topic = "物理"
    elif "化学" in user_text:
        topic = "化学"
    elif "英语" in user_text:
        topic = "英语"
    else:
        topic = "这个内容"

    if stage == "小学阶段":
        return f"""
{topic}听起来有点难，我现在还没学过呢。🌷

如果你想问老师，可以这样说：
**「老师，这个内容我现在还没学过，可以简单告诉我它是什么吗？」**
""".strip()

    if stage == "中学阶段":
        if topic in ("复变函数", "离散数学", "高数", "线性代数", "概率论"):
            return f"""
{topic}我还没学过，听起来像大学数学里的内容。微积分我可能听说过一点，但也没有系统学。🌷

如果你想问老师，可以这样说：
**「老师，这个是不是大学才会学的内容？我现在有点好奇，可以简单了解一下吗？」**
""".strip()
        elif topic == "微积分":
            return f"""
微积分我可能听说过一点，但还没有系统学过，好像是高中后面或者大学会接触的内容。🌷

如果你想向同学请教，可以说：
**「这个我还不太懂，你知道它大概是什么时候会学吗？」**
""".strip()
        else:
            return f"""
{topic}我们正在学/可能会学，不过我主要还是陪你练习校园交流。🌷

如果你想向老师请教，可以这样说：
**「老师，关于{topic}这个部分，我有点跟不上，可以请您再解释一下吗？」**
""".strip()

    if stage == "大学阶段":
        return f"""
{topic}可能有些专业会学，我可以大概聊一点。🌷

不过我这里主要是陪你练习校园交流。如果你想练习请教别人，可以这样说：

**「同学，我最近在看{topic}，有个地方不太明白，你方便帮我讲一下思路吗？」**
""".strip()

    return ""


# =========================
# 4. Qwen 调用
# =========================


def qwen_json_call(system_prompt: str, user_text: str) -> Dict[str, Any]:
    client = get_client()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt + "\n你必须输出 JSON。"},
            {"role": "user", "content": user_text}
        ],
        response_format={"type": "json_object"}
    )
    content = completion.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "role_reply": "我刚刚有点没听清，你可以再说一遍吗？",
            "coach_feedback": "模型没有返回合法 JSON。",
            "hidden_social_meaning": "需要重新生成。",
            "suggested_expression": "你可以说：我想再试一次。",
            "next_prompt": "请再试一次。",
            "risk_level": "未知",
            "raw_output": content
        }


def sanitize_model_reply(text: str) -> str:
    phone_pattern = r"(?<!\d)(?:\+?86[-\s]?)?(?:1[3-9]\d{9}|0\d{2,3}[-\s]?\d{7,8})(?!\d)"
    text = re.sub(phone_pattern, "[官方求助渠道]", text)

    placeholders = ["[姓名]", "[学校/机构]", "[手机号]", "[地址]", "[邮箱]", "[身份证号]", "[QQ号]", "[微信号]"]
    for p in placeholders:
        text = text.replace(p, "")

    text = text.replace("北京24小时心理热线（官方求助渠道）", "当地官方心理援助渠道")
    text = text.replace("北京24小时心理热线", "当地官方心理援助渠道")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# =========================
# 5. Prompt：校园角色扮演 + 训练反馈
# =========================


def build_roleplay_prompt(user_text: str, case: Dict[str, Any]) -> str:
    history_text = format_chat_history(st.session_state.get("chat_history", []))
    latest_user_intent = case.get("latest_user_intent", "")
    force_follow_latest_user = case.get("force_follow_latest_user", False)

    return f"""
你是「慢慢说」校园社交场景预演智能体。

【最高优先级规则】
用户最新输入是：{user_text}

你必须优先回应用户最新说的话，而不是强行回到预设场景。

如果用户最新输入表达了新的需求、感受或话题，例如「我想吃饭」「我不想借了」「我想去厕所」「我有点累」，你要自然接住这个新话题。

预设场景只是背景，不是必须照着演的剧本。
不要每一轮都重新开启原始场景。
不要强行把用户拉回原来的物品、作业、任务或小组活动。

当前是否检测到用户主动换话题：{force_follow_latest_user}
用户主动提出的新意图：{latest_user_intent}

【最近对话历史】
{history_text}

【当前场景背景】
学段：{case.get('stage', '')}
年级：{case.get('grade', '')}
互动类型：{case.get('interaction_type', '')}
你扮演的角色：{case.get('ai_role', '')}
角色姓名：{case.get('ai_name', '')}
角色说话风格：{case.get('ai_style', '')}
校园环境：{case.get('environment', '')}
具体场景：{case.get('scenario', '')}
训练重点：{case.get('training_focus', '')}
沟通目标：{case.get('communication_goal', '')}
本场景参考开场：{case.get('ai_opening_utterance', '')}
用户沉默时可参考：{case.get('ai_followup_if_user_silent', '')}
用户跑题时可参考：{case.get('ai_followup_if_user_offtopic', '')}
用户焦虑时可参考：{case.get('ai_followup_if_user_anxious', '')}
可模仿表达：{case.get('model_ideal_reply', '')}
隐藏教练原则：{case.get('hidden_coach_notes', '')}
安全边界：{case.get('safety_boundary', '')}

【校园学习交流规则】
校园学习交流属于本系统的任务范围。
如果用户询问题目、作业、课堂展示、学习困难、向老师请教、向同学求助等内容，你可以进行简短、清楚、符合当前学段的知识补充。
但不要完全变成通用学科答疑助手。
回答重点应放在：
1. 用户可以怎么向同学或老师表达；
2. 用户可以怎么说明自己哪里不懂；
3. 用户可以怎么准备课堂展示或讲题；
4. 用户可以怎么更自然地参与学习讨论。

【你的回答要求】
1. 像真实同学或老师一样自然接话。
2. 回答要短一点，不要每次都写成说明书。
3. 如果用户换话题，先接住新话题。
4. 如果用户已经在问老师/同学，不要再反复教他说「你可以这样问」，而是直接以当前角色回应。
5. 预设场景只是背景，不是固定剧本。
6. 你不是治疗师，不做医学诊断。
7. 不要输出任何具体电话、热线、非官方链接。
8. 如果用户表达明显自伤或伤害他人风险，risk_level 必须为高，role_reply 应停止角色扮演，建议联系家长、老师、学校心理老师或当地紧急服务。
9. 你必须符合当前学段的真实知识水平和表达方式。小学阶段不要假装理解大学课程；中学阶段不要假装系统学过大学课程；大学阶段可以自然提到大学内容。
10. 只有当用户提出股票、星盘、八字、彩票预测、医疗诊断等与校园学习和校园社交完全无关的问题时，才进行任务边界提醒。

输出要求：严格输出 JSON，不要 Markdown，不要代码块。
JSON 字段必须是：
{{
  "role_reply": "你作为校园角色对学习者说的下一句话，1-2句，必须自然真实",
  "coach_feedback": "给学习者的简短反馈",
  "hidden_social_meaning": "这个场景背后的隐含社交规则或对方真实意图",
  "suggested_expression": "给学习者一句可以直接模仿的表达",
  "next_prompt": "下一步让学习者继续练习的话",
  "risk_level": "低/中/高"
}}
"""


def run_roleplay_agent(user_input: str, case: Dict[str, Any]) -> Dict[str, Any]:
    masked_text, privacy_items = mask_privacy(user_input)
    has_local_crisis = local_crisis_check(user_input)

    system_prompt = build_roleplay_prompt(user_input, case)

    user_payload = {
        "current_user_utterance": masked_text,
        "recent_history": st.session_state.get("chat_history", [])[-8:]
    }

    result = qwen_json_call(system_prompt, json.dumps(user_payload, ensure_ascii=False))

    if has_local_crisis:
        result["risk_level"] = "高"
        result["role_reply"] = "我有点担心你的安全。我们先暂停练习，请马上告诉身边的大人、老师或家长，也可以联系当地紧急服务。"
        result["coach_feedback"] = "检测到高风险表达，系统已暂停角色扮演。"
        result["hidden_social_meaning"] = "当出现安全风险时，优先保护现实安全。"
        result["suggested_expression"] = "我现在很不安全，需要马上找人帮我。"
        result["next_prompt"] = "请先联系现实中的可信任成年人。"

    result["role_reply"] = sanitize_model_reply(str(result.get("role_reply", "")))
    result["privacy_items"] = privacy_items
    result["masked_text"] = masked_text
    return result


# =========================
# 6. 页面渲染
# =========================

ROLE_AVATARS = {
    "同学-同学": "🧒",
    "学生-老师": "👩‍🏫",
    "学生-辅导员": "🧑‍🏫",
    "室友-室友": "🧑",
    "同桌-同桌": "👧",
    "学生-家长": "👨‍👩‍👧",
}


def render_ai_message(text: str, case: Dict[str, Any]):
    avatar = ROLE_AVATARS.get(case.get("interaction_type", ""), "🏫")
    role_name = case.get("ai_name", "校园角色")
    role_type = case.get("ai_role", "")
    stage = case.get("stage", "")
    with st.chat_message("assistant", avatar=avatar):
        st.markdown(
            f"""
            <div class="chat-meta">{avatar} {role_name} · {role_type} · {stage}</div>
            <div class="chat-bubble-ai">{text}</div>
            """,
            unsafe_allow_html=True
        )


def render_user_message(masked_text: str):
    with st.chat_message("user", avatar="🙂"):
        st.markdown(
            f"""
            <div class="chat-meta" style="text-align:right;">🙂 学习者</div>
            <div class="chat-bubble-user">{masked_text}</div>
            """,
            unsafe_allow_html=True
        )


def make_training_report(case: Dict[str, Any], result: Dict[str, Any]) -> str:
    privacy_items = result.get("privacy_items", [])
    privacy_text = "未检测到明显隐私信息。"
    if privacy_items:
        privacy_types = sorted(set([item["type"] for item in privacy_items]))
        privacy_text = "检测并脱敏了以下类型信息：" + "、".join(privacy_types)

    return f"""
# 🌷 校园社交场景预演 · 练习小报告

## 一、训练场景

- 学段：{case.get('stage', '')}
- 年级：{case.get('grade', '')}
- 互动类型：{case.get('interaction_type', '')}
- AI 扮演角色：{case.get('ai_name', '')}（{case.get('ai_role', '')}）
- 校园环境：{case.get('environment', '')}
- 具体场景：{case.get('scenario', '')}
- 难度：{case.get('difficulty_level', '')}
- 训练重点：{case.get('training_focus', '')}
- 沟通目标：{case.get('communication_goal', '')}

## 二、本轮学习者表达，已脱敏

{result.get('masked_text', '')}

## 三、AI 角色回应

{result.get('role_reply', '')}

## 四、简短反馈

{result.get('coach_feedback', '')}

## 五、隐含社交含义

{result.get('hidden_social_meaning', '')}

## 六、可模仿表达

{result.get('suggested_expression', '')}

## 七、下一步练习

{result.get('next_prompt', '')}

## 八、隐私处理说明

{privacy_text}

## 九、安全边界

本系统用于校园社交场景预演和沟通练习，不用于医学诊断、治疗或宣称改善自闭症核心症状。建议在家长、教师或专业人员指导下使用。
""".strip()


# =========================
# 7. Streamlit 主界面
# =========================

apply_soft_theme()

# ── Hero 区块 ──
st.markdown("""
<div class="hero-wrap">
    <div class="hero-card">
        <div class="hero-badge">🫧 今天也可以慢慢开口</div>
        <div class="hero-title">🌷 慢慢说：校园社交场景预演智能体</div>
        <div class="hero-subtitle">
            在温柔、低刺激的练习环境里，提前熟悉校园中的真实交流方式。<br>
            就算只说一句话，也是一种勇敢。
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 步骤引导 ──
st.markdown("""
<div class="step-box">
<b>✨ 今天怎么练习？</b><br>
① 选择学段 → ② 选择练习对象 → ③ 选择练习重点 → ④ 抽取场景 → ⑤ 开始对话 → ⑥ 查看温柔反馈
</div>
""", unsafe_allow_html=True)

# 读取数据集
df = load_roleplay_dataset(str(DATA_PATH))

if df.empty:
    st.error(
        "没有找到数据集文件。请把 realistic_school_roleplay_asd_5000.csv 放到 app.py 同一个文件夹下，然后重新运行。"
    )
    st.stop()


def reset_training_state():
    """当用户切换筛选条件时，清空旧场景和旧对话。"""
    st.session_state.current_case = None
    st.session_state.chat_history = []
    st.session_state.last_result = None
    st.session_state.last_academic_topic = None


with st.sidebar:
    st.header("🌈 练习设置")

    st.markdown("""
    <div class="cute-card">
    <b>🌼 今天的小提醒</b><br>
    你不需要一次做得很好，只要比刚才更敢表达一点点，就已经很棒了。
    </div>
    """, unsafe_allow_html=True)

    stage_options = ["不限"] + get_unique_options(df, "stage")
    stage = st.selectbox("🎓 练习学段", stage_options, index=0, key="stage_select", on_change=reset_training_state)

    interaction_options = ["不限"] + get_unique_options(df, "interaction_type")
    interaction_type = st.selectbox("👥 练习对象", interaction_options, index=0, key="interaction_select", on_change=reset_training_state)

    # 校园环境合并为常见分类
    env_options = ["不限"] + ENVIRONMENT_OPTIONS
    environment = st.selectbox("📍 校园环境", env_options, index=0, key="env_select", on_change=reset_training_state)

    # 训练重点简化为 4 大类
    focus_options = ["不限", "开始对话", "回应别人", "请求帮助", "表达拒绝或不舒服"]
    training_focus = st.selectbox(
        "🌼 今天想练习什么？",
        focus_options,
        index=0,
        key="focus_select",
        on_change=reset_training_state,
        help=(
            "开始对话：打招呼、加入聊天、主动开口\n\n"
            "回应别人：回答问题、回应邀请、回应提醒\n\n"
            "请求帮助：听不懂、不会做、需要帮忙\n\n"
            "表达拒绝或不舒服：不想参加、感到紧张、想休息"
        )
    )

    filtered = filter_dataset(df, stage, interaction_type, environment, training_focus)

    if st.button("🎲 抽取 / 切换一个训练场景"):
        if filtered.empty:
            st.warning("当前条件下没有匹配场景，请放宽筛选条件。")
        else:
            st.session_state.current_case = select_case(filtered)
            st.session_state.chat_history = []
            st.session_state.last_result = None
            st.rerun()

    if st.button("🔄 重新开始今天的练习"):
        st.session_state.chat_history = []
        st.session_state.last_result = None
        st.rerun()



if "current_case" not in st.session_state:
    st.session_state.current_case = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_academic_topic" not in st.session_state:
    st.session_state.last_academic_topic = None

# 当筛选条件改变后 current_case 被清空，自动抽取新场景
if st.session_state.current_case is None:
    if not filtered.empty:
        st.session_state.current_case = select_case(filtered)

case = st.session_state.current_case

# 保险：如果当前场景与已选的筛选条件不一致，强制清空重抽
if case is not None and case:
    cond_stage = (stage == "不限" or case.get("stage") == stage)
    cond_interaction = (interaction_type == "不限" or case.get("interaction_type") == interaction_type)
    if environment == "不限":
        cond_env = True
    else:
        mapped_envs = map_environment(environment)
        cond_env = case.get("environment") in mapped_envs if mapped_envs else True

    if not (cond_stage and cond_interaction and cond_env):
        st.session_state.current_case = select_case(filtered) if not filtered.empty else {}
        st.session_state.chat_history = []
        st.session_state.last_result = None
        case = st.session_state.current_case

# 如果没有匹配场景，显示友好提示
if not case or case == {}:
    st.info("👋 当前筛选条件下还没有匹配的练习场景，请在左侧调整学段、练习对象或校园环境，然后点击「抽取场景」按钮。")
    st.stop()

# 一句温柔提示
st.markdown("""
<div style="text-align:center;color:#8C8799;font-size:15px;margin:8px 0 16px 0;">
🌷 已为你准备好一个校园练习场景。你可以慢慢回应，不用一次说得很好。
</div>
""", unsafe_allow_html=True)

# 如果刚进入场景，先展示 AI 开场白
if not st.session_state.chat_history:
    opening = case.get("ai_opening_utterance", "你好，我们来练习这个校园场景吧。")
    render_ai_message(opening, case)

# 展示历史消息
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        render_user_message(msg["content"])
    elif msg["role"] == "assistant":
        render_ai_message(msg["content"], case)

user_input = st.chat_input("💭 试着回应这个校园角色吧。可以只说一句，也可以说「我不知道怎么回答」，没关系的。")

if user_input:
    # ── 第〇层：检测用户是否主动换话题，记录到 case 中供 prompt 使用 ──
    if is_user_topic_shift(user_input):
        case["latest_user_intent"] = user_input
        case["force_follow_latest_user"] = True
    else:
        case["latest_user_intent"] = ""
        case["force_follow_latest_user"] = False
    st.session_state.current_case = case

    # ── 第一层：校园学习交流（允许回答，优先处理）──
    if is_school_study_communication(user_input):
        masked_text, privacy_items = mask_privacy(user_input)
        role_reply = build_study_communication_reply(masked_text, case)

        render_user_message(masked_text)
        render_ai_message(role_reply, case)

        st.session_state.chat_history.append({"role": "user", "content": masked_text})
        st.session_state.chat_history.append({"role": "assistant", "content": role_reply})
        st.session_state.last_result = {
            "masked_text": masked_text,
            "role_reply": role_reply,
            "coach_feedback": "检测到校园学习交流内容，已提供符合当前学段的简短讲解和沟通练习引导。",
            "hidden_social_meaning": "向同学/老师请教学习问题，是校园社交中非常常见且重要的一类场景。",
            "suggested_expression": "我这个地方有点不懂，你能不能先给我讲一下思路？",
            "next_prompt": "你可以试着模仿上面的表达，或者继续说你想练习的校园场景。",
            "risk_level": "低",
            "privacy_items": privacy_items,
        }
        st.stop()

    # ── 第二层：明显无关问题（股票、代码、星盘等）──
    if is_out_of_scope(user_input):
        masked_text, privacy_items = mask_privacy(user_input)
        role_reply = build_boundary_reply(masked_text, case)

        render_user_message(masked_text)
        render_ai_message(role_reply, case)

        st.session_state.chat_history.append({"role": "user", "content": masked_text})
        st.session_state.chat_history.append({"role": "assistant", "content": role_reply})
        st.session_state.last_result = {
            "masked_text": masked_text,
            "role_reply": role_reply,
            "coach_feedback": "本轮用户输入偏离了校园社交练习范围，系统已温和引导回练习主题。",
            "hidden_social_meaning": "识别对话边界也是一种社交能力。",
            "suggested_expression": "我想练习怎么向老师/同学开口。",
            "next_prompt": "如果你准备好了，可以直接在对话框里说你想练习什么场景。",
            "risk_level": "低",
            "privacy_items": privacy_items,
        }
        st.stop()

    # ── 第三层：角色知识询问（你学过XX吗？）──
    if is_asking_role_knowledge(user_input):
        masked_text, privacy_items = mask_privacy(user_input)
        role_reply = build_role_knowledge_reply(masked_text, case)

        render_user_message(masked_text)
        render_ai_message(role_reply, case)

        st.session_state.chat_history.append({"role": "user", "content": masked_text})
        st.session_state.chat_history.append({"role": "assistant", "content": role_reply})
        st.session_state.last_result = {
            "masked_text": masked_text,
            "role_reply": role_reply,
            "coach_feedback": "检测到用户在询问角色的学科知识背景，已根据当前学段生成符合角色身份的回应。",
            "hidden_social_meaning": "不同学段的角色有不同的知识边界，保持角色真实性也是一种社交示范。",
            "suggested_expression": "我想练习怎么向老师/同学请教这个问题。",
            "next_prompt": "你可以试着模仿上面的表达，或者继续说你想练习的校园场景。",
            "risk_level": "低",
            "privacy_items": privacy_items,
        }
        st.stop()

    # ── 第四层：正常校园角色扮演 ──
    with st.spinner("🌷 正在为你准备回应：保护隐私 → 理解场景 → 温柔对话 → 练习反馈..."):
        result = run_roleplay_agent(user_input, case)

    masked_text = result.get("masked_text", user_input)
    role_reply = result.get("role_reply", "")

    render_user_message(masked_text)
    render_ai_message(role_reply, case)

    st.session_state.chat_history.append({"role": "user", "content": masked_text})
    st.session_state.chat_history.append({"role": "assistant", "content": role_reply})
    st.session_state.last_result = result
