# Music Workshop — AI 辅助作曲桌面软件

## 项目概述
Python + PySide6 桌面应用，通过波形合成模拟乐器音色，支持键盘作曲和五线谱显示。

## 技术栈
- **语言**: Python 3.11+
- **GUI**: PySide6 (Qt6)
- **音频**: numpy + sounddevice (自实现合成器，无 pyo)
- **乐谱**: music21 + VexFlow (QWebEngineView)
- **测试**: pytest

## 目录结构
```
music_workshop/
├── main.py                  # 入口
├── pyproject.toml
├── music_workshop/
│   ├── audio/               # 音频引擎（零 Qt 依赖）
│   │   ├── engine.py        # AudioEngine: sounddevice 流
│   │   ├── mixer.py         # Mixer: 声部池管理
│   │   ├── voice.py         # Voice: 合成器+包络
│   │   ├── envelope.py      # ADSREnvelope
│   │   └── synths/          # 合成器实现
│   │       ├── base.py      # BaseSynthesizer ABC
│   │       ├── karplus_strong.py  # Phase 1
│   │       ├── fm.py        # Phase 3
│   │       ├── additive.py  # Phase 3
│   │       └── modal.py     # Phase 3
│   ├── instruments/          # 乐器预设
│   ├── input/                # 键盘输入、量化、录音
│   ├── score/                # 乐谱管理、导出
│   ├── ui/                   # 界面组件
│   └── resources/            # HTML资源
└── tests/
```

## 分阶段实施

### Phase 1 ✅ 完成 — 核心合成器 + 键盘演奏
- Karplus-Strong 合成器（钢琴、吉他等拨弦乐器）
- ADSR 包络、Voice、Mixer、AudioEngine
- 键盘→MIDI 映射 (QWERTY)
- 钢琴键盘可视化控件
- 4 种基础乐器预设

### Phase 2 — 录音 + 五线谱
- Quantizer (可调量化精度)
- Recorder (录音→乐谱)
- ScoreManager (music21 封装)
- VexFlow 五线谱渲染

### Phase 3 — 乐器扩展 + 效果器
- FM 合成、加法合成、模态合成
- 混响/合唱效果器
- 6+ 种乐器预设

### Phase 4 — 专业工具
- MIDI/MusicXML/LilyPond 导出
- 多轨分谱、撤销/重做、项目保存

### Phase 5 — AI 辅助作曲
- LLM 集成、旋律续写、和弦推荐

## 核心架构原则
1. `audio/` 包零 Qt 依赖 — 纯 numpy + sounddevice，可独立测试
2. 音频回调线程永不阻塞 — 不分配内存、不持锁、不 I/O
3. 乐器预设即配置 — 所有乐器 = 参数 + 合成器类型
4. 增量迭代 — 每个 Phase 都是可用的里程碑

## 乐器声波设计
每种乐器由三层定义：
1. **合成算法** (KS/FM/加法/模态) — 决定谐波结构
2. **ADSR 包络** — 决定音量轮廓
3. **效果链** — 增加空间感和厚度

详细参数见 `music_workshop/instruments/presets.py`

## 运行方式
```bash
# 虚拟环境
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"

# 运行
python main.py

# 测试
pytest tests/ -v
```
