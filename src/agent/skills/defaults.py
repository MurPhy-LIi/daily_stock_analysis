# -*- coding: utf-8 -*-
"""
Shared defaults for trading skills.

This module centralises:
1. The default active skill set used by agent entrypoints
2. The fallback skill subset used by the multi-agent router
3. Common prompt fragments that previously drifted across multiple files
4. Helper utilities for skill-specific agent naming
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional


_BUILTIN_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "strategies"

SKILL_AGENT_PREFIX = "skill_"
LEGACY_STRATEGY_AGENT_PREFIX = "strategy_"
SKILL_CONSENSUS_AGENT_NAME = "skill_consensus"
LEGACY_STRATEGY_CONSENSUS_AGENT_NAME = "strategy_consensus"

CORE_TRADING_SKILL_POLICY_ZH = """## 美股事实优先监控基线（必须严格遵守）

本报告的定位是“每日事实监控与投资论点更新”，不是自动交易系统。
分析重点必须是可核查事实、基本面变化、产业链影响与待验证问题。
技术指标只作为辅助背景，不能单独产生买入、卖出、目标价或仓位结论。

### 1. 证据优先级

事实来源按以下顺序排序：

1. 公司 Investor Relations、SEC 文件、交易所或监管公告
2. 公司管理层公开发言、财报电话会和正式新闻稿
3. Reuters、Bloomberg、Financial Times、Wall Street Journal 等可靠媒体
4. 行业媒体和可靠数据机构
5. 搜索聚合页面、分析师评论和二手转载

若输入中没有提供来源名称、发布日期或链接，不得把内容写成已确认事实。
必须明确区分：
- 已验证事实
- 媒体报道
- 分析师观点
- 模型推断
- 尚待验证的信息

严禁虚构来源、日期、目标价、市场份额、机构持仓或公司公告。

### 2. 数据质量硬护栏

出现下列任一情况时：

- quote 状态为 fallback、missing 或 stale
- technical 状态为 partial、missing 或 fetch_failed
- 当前价、昨收、涨跌额和涨跌幅无法互相验证
- 行情时间戳不明确
- 财务数据期间或口径不明确
- 新闻缺乏可追溯来源

必须执行以下规则：

- decision_type 默认使用 hold
- operation_advice 使用“数据不足，继续观察”
- 不提供具体买入点、卖出点、目标价或仓位比例
- stop_loss 填写“数据质量不足，不提供机械止损位”
- target_price 填写“缺乏可靠估值依据，不提供”
- position_strategy 填写“仅监控，不提供仓位建议”
- 必须在 data_limitations 中逐项说明缺失或矛盾
- 不得以“数据质量评分较高”为理由忽略上述限制

如果价格字段存在数学矛盾，必须明确指出矛盾，而不是选择其中一个继续分析。

### 3. 技术面的权重限制

技术面总权重不得超过20%。

MA5、MA10、MA20、RSI、MACD和成交量只能用于说明：
- 短期价格状态
- 波动是否扩大
- 市场是否已经反映部分信息

不得仅因：
- 多头排列而建议买入
- 空头排列而建议卖出
- 回踩MA5或MA10而生成买点
- 跌破MA20而生成机械止损
- RSI超卖而建议抄底

不得使用“完美多头排列”“严禁抄底”“坚决清仓”等无条件语言。

### 4. 每日分析的核心问题

每家公司优先回答：

1. 最近发生了什么可验证的新事实？
2. 该事实与上一期财报、管理层指引或市场预期相比有什么变化？
3. 对收入、毛利率、资本开支、现金流或竞争格局可能产生什么影响？
4. 对所处产业链的需求、供给、瓶颈和定价权有什么影响？
5. 原有投资论点是增强、削弱、无明显变化，还是暂时无法判断？
6. 接下来需要验证哪些具体指标、公告或管理层表述？

### 5. AI基础设施公司的行业分析

对于AI基础设施相关公司，应根据公司业务选择相关指标：

- GPU/加速器：产品出货、架构升级、供应约束、客户CapEx、竞争产品
- HBM/存储：ASP、bit shipment、产能、客户认证、库存、CapEx和供需周期
- 网络/光互联：端口速率、交换机和光模块需求、CPO、客户集中度
- 数据中心：签约容量、在建容量、电力获取、资本成本和交付周期
- 电力设备：订单、backlog、产能扩张、交付周期和定价
- 云厂商：AI CapEx、折旧、云收入、AI收入转化和自由现金流压力

没有相应数据时必须写“尚无足够数据”，不得用泛泛的AI叙事填补。

### 6. 财务数据规则

- 明确区分单季度、财年累计、TTM和年度数据
- 明确区分GAAP和non-GAAP
- 不得把季度数字描述成全年数字
- 异常高的净利润、ROE、经营现金流或增长率必须检查非经常性项目
- 不能因为ROE很高，就直接得出估值合理或基本面确定性高
- 缺少PE、FCF、股本、净现金或盈利预测时，不得给出估值结论
- 所有美股货币单位使用“美元”，不得写成“元”

### 7. 新闻与产业事实输出

每条重要事件应尽可能包含：
- 日期
- 事件主体
- 事实描述
- 来源名称
- 来源等级
- 对投资论点的影响
- 尚待验证之处

分析师目标价只能标记为“分析师观点”，不能作为模型目标价。
13F持仓变化只能说明上一季度披露的持仓，不得描述为当日新建仓。

### 8. 最终结论

最终结论只允许使用：

- 投资论点增强
- 投资论点轻微增强
- 无明显变化
- 投资论点轻微削弱
- 投资论点削弱
- 数据不足，无法判断

analysis_summary 和 dashboard.core_conclusion.one_sentence
必须以以上六种投资论点状态之一开头，再解释依据。

默认不提供直接买卖指令。

只有在行情、财务、新闻和估值证据均可验证且彼此一致时，才可讨论行动条件；即使如此，也必须使用条件式语言，不得输出确定性仓位指令。

报告的首要目标是减少信息遗漏和识别需要进一步研究的事项，而不是预测下一交易日涨跌。
"""
TECHNICAL_SKILL_RULES_EN = """## Fact-First Technical Context Baseline

Technical indicators are secondary descriptive context, not independent
buy, sell, position-sizing, target-price, or stop-loss signals.

- The total technical-analysis weight must not exceed 20%.
- MA5, MA10, MA20, RSI, MACD, and volume may only describe short-term
  price behavior, volatility, and market positioning.
- Do not recommend buying solely because of bullish moving-average alignment.
- Do not recommend selling solely because of bearish moving-average alignment.
- Do not generate an entry because price touches MA5 or MA10.
- Do not generate a mechanical stop-loss because price falls below MA20.
- Do not recommend bottom-fishing solely because RSI is oversold.
- Avoid absolute language such as "must buy", "must sell", "never buy",
  or "liquidate immediately".

If quote status is fallback, missing, or stale, or technical status is
partial, missing, or fetch_failed:

- Treat technical conclusions as unreliable.
- Do not provide precise entry prices, exit prices, target prices,
  stop-loss prices, or position percentages.
- Explicitly state that the available market data is insufficient.
- Default to monitoring rather than issuing a trading instruction.

Before interpreting price movement, verify that current price,
previous close, price change, and percentage change are mathematically
consistent. If they are inconsistent, identify the contradiction and
do not use the affected fields for decision-making.
"""

def get_default_trading_skill_policy(*, explicit_skill_selection: bool) -> str:
    """Return the legacy default trading baseline only for implicit/default runs.

    When a caller explicitly chooses a skill (via request payload or config),
    analysis should follow that selected skill alone instead of silently
    layering the old bull-trend baseline on top.
    """
    if explicit_skill_selection:
        return ""
    return CORE_TRADING_SKILL_POLICY_ZH


def get_default_technical_skill_policy(*, explicit_skill_selection: bool) -> str:
    """Return the technical-agent baseline only for implicit/default runs."""
    if explicit_skill_selection:
        return ""
    return TECHNICAL_SKILL_RULES_EN


@lru_cache(maxsize=1)
def _load_builtin_skill_catalog() -> tuple[object, ...]:
    try:
        from src.agent.skills.base import load_skills_from_directory

        return tuple(load_skills_from_directory(_BUILTIN_SKILLS_DIR))
    except Exception:
        return ()


def _coerce_priority(value: object, default: int = 100) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_available_ids(available_skill_ids: Optional[Iterable[str]]) -> List[str]:
    normalized: List[str] = []
    if available_skill_ids is None:
        return normalized
    for skill_id in available_skill_ids:
        if isinstance(skill_id, str):
            cleaned = skill_id.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
    return normalized


def _normalize_skill_inputs(
    skills: Optional[Iterable[object]],
    available_skill_ids: Optional[Iterable[str]] = None,
) -> tuple[List[object], List[str]]:
    normalized_available = _normalize_available_ids(available_skill_ids)

    if skills is None:
        return list(_load_builtin_skill_catalog()), normalized_available

    skill_pool: List[object] = []
    for item in skills:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned and cleaned not in normalized_available:
                normalized_available.append(cleaned)
            continue
        if item is not None:
            skill_pool.append(item)
    return skill_pool, normalized_available


def _sort_skill_pool(skills: Iterable[object]) -> List[object]:
    return sorted(
        skills,
        key=lambda skill: (
            _coerce_priority(getattr(skill, "default_priority", 100)),
            str(getattr(skill, "display_name", "") or getattr(skill, "name", "")),
            str(getattr(skill, "name", "")),
        ),
    )


def _iter_candidate_skills(
    skills: Optional[Iterable[object]],
    *,
    available_skill_ids: Optional[Iterable[str]] = None,
    user_invocable_only: bool = True,
) -> tuple[List[object], List[str]]:
    skill_pool, normalized_available = _normalize_skill_inputs(skills, available_skill_ids)
    available_lookup = set(normalized_available)

    candidates: List[object] = []
    for skill in _sort_skill_pool(skill_pool):
        skill_id = str(getattr(skill, "name", "")).strip()
        if not skill_id:
            continue
        if user_invocable_only and not bool(getattr(skill, "user_invocable", True)):
            continue
        if available_lookup and skill_id not in available_lookup:
            continue
        candidates.append(skill)

    return candidates, normalized_available


def _slice_skill_ids(skill_ids: List[str], max_count: Optional[int]) -> List[str]:
    if max_count is None:
        return skill_ids
    return skill_ids[:max_count]


def _pick_primary_default_skill_id(candidates: List[object]) -> str:
    preferred = [
        str(getattr(skill, "name", "")).strip()
        for skill in candidates
        if bool(getattr(skill, "default_active", False))
    ]
    if preferred:
        return preferred[0]

    fallback = [str(getattr(skill, "name", "")).strip() for skill in candidates]
    if fallback:
        return fallback[0]

    return ""


def get_default_active_skill_ids(
    skills: Optional[Iterable[object]] = None,
    max_count: Optional[int] = None,
    available_skill_ids: Optional[Iterable[str]] = None,
) -> List[str]:
    candidates, normalized_available = _iter_candidate_skills(
        skills,
        available_skill_ids=available_skill_ids,
    )
    default_skill_id = _pick_primary_default_skill_id(candidates)
    if default_skill_id:
        return _slice_skill_ids([default_skill_id], max_count)

    return _slice_skill_ids(normalized_available[:1], max_count)


def get_default_router_skill_ids(
    skills: Optional[Iterable[object]] = None,
    max_count: Optional[int] = None,
    available_skill_ids: Optional[Iterable[str]] = None,
) -> List[str]:
    candidates, normalized_available = _iter_candidate_skills(
        skills,
        available_skill_ids=available_skill_ids,
    )
    preferred = [
        str(getattr(skill, "name", "")).strip()
        for skill in candidates
        if bool(getattr(skill, "default_router", False))
    ]
    if preferred:
        return _slice_skill_ids(preferred, max_count)

    return get_default_active_skill_ids(
        candidates,
        max_count=max_count,
        available_skill_ids=normalized_available,
    )


def get_regime_skill_ids(
    regime: str,
    skills: Optional[Iterable[object]] = None,
    max_count: Optional[int] = None,
    available_skill_ids: Optional[Iterable[str]] = None,
) -> List[str]:
    candidates, normalized_available = _iter_candidate_skills(
        skills,
        available_skill_ids=available_skill_ids,
    )
    regime_name = (regime or "").strip().lower()
    if regime_name:
        matched = []
        for skill in candidates:
            market_regimes = getattr(skill, "market_regimes", None) or []
            normalized_regimes = {
                str(item).strip().lower()
                for item in market_regimes
                if str(item).strip()
            }
            if regime_name in normalized_regimes:
                matched.append(str(getattr(skill, "name", "")).strip())
        if matched:
            return _slice_skill_ids(matched, max_count)

    return get_default_router_skill_ids(
        candidates,
        max_count=max_count,
        available_skill_ids=normalized_available,
    )


def get_primary_default_skill_id(
    skills: Optional[Iterable[object]] = None,
    available_skill_ids: Optional[Iterable[str]] = None,
) -> str:
    defaults = get_default_active_skill_ids(skills, max_count=1, available_skill_ids=available_skill_ids)
    return defaults[0] if defaults else ""


def _build_regime_skill_ids(skills: Iterable[object]) -> Dict[str, List[str]]:
    regime_map: Dict[str, List[str]] = {}
    for skill in _sort_skill_pool(skills):
        skill_id = str(getattr(skill, "name", "")).strip()
        if not skill_id:
            continue
        for regime in getattr(skill, "market_regimes", None) or []:
            regime_name = str(regime).strip().lower()
            if not regime_name:
                continue
            regime_map.setdefault(regime_name, []).append(skill_id)
    return regime_map


DEFAULT_ACTIVE_SKILL_IDS: tuple[str, ...] = tuple(get_default_active_skill_ids())
DEFAULT_ROUTER_SKILL_IDS: tuple[str, ...] = tuple(get_default_router_skill_ids())
PRIMARY_DEFAULT_SKILL_ID = get_primary_default_skill_id()
REGIME_SKILL_IDS: Dict[str, List[str]] = _build_regime_skill_ids(_load_builtin_skill_catalog())


def build_skill_agent_name(skill_id: str) -> str:
    return f"{SKILL_AGENT_PREFIX}{skill_id}"


def extract_skill_id(agent_name: Optional[str]) -> Optional[str]:
    if not agent_name or not isinstance(agent_name, str):
        return None
    for prefix in (SKILL_AGENT_PREFIX, LEGACY_STRATEGY_AGENT_PREFIX):
        if agent_name.startswith(prefix):
            return agent_name[len(prefix):]
    return None


def is_skill_agent_name(agent_name: Optional[str]) -> bool:
    return extract_skill_id(agent_name) is not None


def is_skill_consensus_name(agent_name: Optional[str]) -> bool:
    return agent_name in {SKILL_CONSENSUS_AGENT_NAME, LEGACY_STRATEGY_CONSENSUS_AGENT_NAME}
