# 🎹 Music Workshop — AI 辅助作曲桌面软件

> **用键盘作曲，用波形造音，用 AI 写歌。**  
> 一个从零合成乐器波形、用电脑键盘弹琴作曲、可视化五线谱的桌面音乐创作工具。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ 核心功能

### 🎸 专业乐器模拟（纯波形合成）
不依赖任何采样库，通过数学算法直接生成声波来模拟真实乐器音色：

| 合成方法 | 原理 | 适用乐器 | 真实度 |
|---------|------|---------|--------|
| **Karplus-Strong** | 延迟线 + 低通反馈，模拟拨弦物理 | 钢琴、吉他、竖琴 | 60-70% |
| **FM 合成** | 频率调制产生丰富泛音 | 电钢、铜管、贝斯 | Phase 3 |
| **加法合成** | 叠加多个谐波正弦波 | 管风琴、弦乐 | Phase 3 |
| **模态合成** | 多个谐振模式 + 激励噪声 | 马林巴、钟琴 | Phase 3 |

> 合成音色约能达到真实乐器的 60-70%，对作曲编曲来说完全足够。之后可通过多层 KS + 混合采样进一步提升。

### ⌨️ 键盘作曲
用电脑键盘像弹钢琴一样输入旋律：

```
白键（F 行）：Z→C4  X→D4  C→E4  V→F4  B→G4  N→A4  M→B4  ,→C5  .→D5  /→E5
黑键（D 行）：A→C#4  S→D#4  D→F#4  F→G#4  G→A#4  H→C#5  J→D#5  K→F#5  L→G#5  ;→A#5
```

- **升降八度**：Shift+Z（降）/ Shift+X（升）
- **力度控制**：Ctrl=弱 (60)，Alt=中 (80)，默认=强 (100)
- **量化精度可调**：全音符到 32 分音符，适配不同水平的输入精度

### 🎼 五线谱实时渲染
录音后自动生成标准五线谱（VexFlow 引擎），支持：
- 实时音符显示（录一个音刷新一次）
- 多种量化精度适配
- MIDI / MusicXML / LilyPond 导出（可用 MuseScore 打开编辑）

### 🤖 AI 辅助作曲（规划中）
- 本地 LLM 集成（Ollama/Llama.cpp）
- 旋律续写 → 和弦推荐 → 自动和声化

---

## 🧱 技术栈

| 层 | 技术 | 选型理由 |
|---|---|---|
| **语言** | Python 3.11+ | 生态丰富、开发快 |
| **GUI** | PySide6 (Qt6) | 原生桌面、QPainter 绘图、QWebEngineView |
| **音频引擎** | numpy + sounddevice | 实时音频、低延迟、纯 Python DSP |
| **合成器** | 自实现 (numpy) | 完全掌控波形生成逻辑 |
| **乐谱渲染** | music21 + VexFlow | 专业乐谱数据模型 + 浏览器级渲染 |
| **MIDI** | mido + python-rtmidi | MIDI 键盘支持与文件导入导出 |

---

## 📁 项目结构

```
music_workshop/
├── main.py                        # 程序入口
├── pyproject.toml                 # 依赖配置
│
├── music_workshop/
│   ├── app.py                     # 应用配置
│   │
│   ├── audio/                     # 音频引擎（纯 numpy，零 Qt 依赖）
│   │   ├── engine.py              # AudioEngine — sounddevice 实时音频流
│   │   ├── mixer.py              # Mixer — 32声部池管理
│   │   ├── voice.py              # Voice — 合成器+包络封装
│   │   ├── envelope.py           # ADSREnvelope — 四段包络
│   │   └── synths/
│   │       ├── base.py           # BaseSynthesizer (ABC)
│   │       └── karplus_strong.py # Karplus-Strong 物理建模
│   │
│   ├── instruments/
│   │   ├── registry.py           # 乐器注册表/工厂
│   │   └── presets.py            # 内置乐器预设（钢琴/吉他等）
│   │
│   ├── input/
│   │   ├── keyboard_mapper.py    # QWERTY 键盘 → MIDI 音符
│   │   ├── quantizer.py          # 音符时值量化器
│   │   └── recorder.py           # 录音器（按键→乐谱）
│   │
│   ├── score/
│   │   ├── score_manager.py      # music21 乐谱管理器（多轨+撤销）
│   │   ├── export.py             # VexFlow JSON 导出
│   │   ├── importer.py           # MIDI 文件导入
│   │   ├── undo_manager.py       # 撤销/重做引擎
│   │   └── project.py            # 项目文件保存/加载 (.mwproj)
│   │
│   ├── ai/                        # AI 辅助作曲（Phase 5）
│   │   ├── client.py             # DeepSeek API 客户端（OpenAI 兼容）
│   │   ├── melody.py             # 旋律续写助手
│   │   └── harmony.py            # 和弦推荐助手
│   │
│   ├── ui/
│   │   ├── main_window.py        # 主窗口
│   │   ├── piano_widget.py       # 钢琴键盘可视化控件
│   │   ├── notation_view.py      # 五线谱显示 (QWebEngineView)
│   │   ├── instrument_panel.py   # 乐器选择面板
│   │   └── transport_bar.py      # 传输控制栏
│   │
│   └── resources/
│       └── vexflow_renderer.html # VexFlow 五线谱渲染页面
│
└── tests/
```

---

## 🚀 快速开始

### 前置条件
- Python 3.11+
- 声卡（任何电脑都有）

### 安装

```bash
# 克隆项目
git clone https://github.com/yourname/music-workshop.git
cd music-workshop

# 创建虚拟环境（隔离系统包）
python -m venv .venv

# 安装核心依赖
.venv/Scripts/pip install PySide6 numpy sounddevice music21

# AI 作曲功能需要（可选）
.venv/Scripts/pip install openai

# 运行！
.venv/Scripts/python main.py
```

### 使用指南

```
1. ⏺ 按 Record 按钮开始录音
2. 🎹 用键盘弹旋律（Z/X/C/V = C/D/E/F...）
3. ⏹ 再按 Record 停止
4. 🎼 五线谱自动生成！
5. 🎸 在 Instrument 面板切换乐器音色
6. 🎛 调整 BPM 和量化精度控制谱面精度
7. 💾 按 Save 保存项目 (.mwproj)，Load 打开
8. 🎵 按 MIDI 导出标准 MIDI 文件
9. 🤖 在 AI Composer 面板：
   - 「Suggest Continuation」→ AI 续写旋律
   - 「Suggest Chords」→ AI 推荐和弦
   - 选一个建议点 Apply 应用
```

### 配置 DeepSeek AI（可选）

```bash
# 设置 API 密钥（没有的话 AI 会使用算法 fallback）
export DEEPSEEK_API_KEY=your_key_here
# Windows CMD:
set DEEPSEEK_API_KEY=your_key_here
# Windows PowerShell:
$env:DEEPSEEK_API_KEY="your_key_here"

.venv/Scripts/python main.py
```

---

## 🗺 开发路线图

| 阶段 | 里程碑 | 完成 |
|------|--------|------|
| **Phase 1** 🔥 | **能发声** — KS 合成器 + 键盘映射 + 钢琴控件 | ✅ |
| **Phase 2** 🔥 | **能看谱** — 录音 + 量化 + 五线谱渲染 | ✅ |
| **Phase 3** 🔥 | **乐团** — FM/加法/模态合成 + 10乐器 + 混响/合唱效果器 | ✅ |
| **Phase 4** 🔥 | **作曲工作台** — MIDI 导入导出、多轨分谱、撤销/重做、项目保存 | ✅ |
| **Phase 5** 🔥 | **AI 作曲家** — DeepSeek API 旋律续写、和弦推荐 | ✅ |

---

## ⚙️ 波形合成原理（核心）

每种乐器由**三个层面**定义：

```
乐器音色 = 合成算法(参数) × ADSR包络 + 效果链
```

以钢琴为例（Karplus-Strong）：

```
初始化延迟线：buffer = random[-0.5, 0.5] × 168 个采样 (C4)
每个采样点：
  output = buffer[idx]                    ← 输出当前值
  avg = 0.7×buffer[idx] + 0.3×buffer[idx+1]  ← 低通滤波
  buffer[idx] = avg × 0.998              ← 衰减回写
  idx = (idx + 1) % 168                  ← 循环递进
```

这模拟了琴弦的物理振动：**随机初始激励 → 高频快速衰减 → 持续发声 → 缓慢消失**。

合成波形与真实钢琴波形的对比：

| 方面 | 合成（KS） | 真实钢琴 | 差距 |
|------|-----------|---------|------|
| 起音瞬态 | 随机噪声→滤波 | 音槌击弦复杂瞬态 | ⚠️ 有差距 |
| 泛音结构 | 平滑指数衰减 | 精细谐波峰谷 | ⚠️ 可感知 |
| 音高/衰减 | ✅ 准确 | ✅ 准确 | ✅ 一致 |
| 和弦/多音 | ✅ 独立声部 | ✅ 独立琴弦 | ✅ 一致 |

> 对作曲编曲来说足够用，追求极致可叠加击槌噪声模型 + 多层 KS。

---

## 🔧 架构设计

### 线程模型
```
┌─────────────────────────────────────────────────┐
│  UI 线程（Qt 主循环）                             │
│  - 界面绘制、键盘事件、Signal/Slot                 │
│  - 永不阻塞 >5ms                                  │
└──────────────┬──────────────────────────────────┘
               │ Queue (线程安全)
               ▼
┌─────────────────────────────────────────────────┐
│  音频回调线程（PortAudio 实时线程）                  │
│  - 每 ~5.3ms 调用一次                             │
│  - 不分配内存、不持锁、不 I/O                       │
│  - 从 Queue 接收事件 → 混合音频 → 写入声卡缓冲区     │
└─────────────────────────────────────────────────┘
```

### 数据流

```
键盘输入 → PianoWidget → AudioEngine (发声)
                         └→ Recorder (录音)
                              ↓
                          Quantizer (量化)
                              ↓
                        ScoreManager (乐谱)
                              ↓
                        VexFlow JSON → NotationView (显示)
```

---

## 🤝 贡献

这是一个开放的个人项目。如果你想参与：
1. Fork 项目
2. 创建你的特性分支 (`git checkout -b feature/amazing`)
3. Commit 你的改动
4. Push 到分支
5. 提交 Pull Request

---

## 📄 许可

MIT License

---

## 🙏 致谢

- [VexFlow](https://vexflow.com/) — 专业的五线谱 JavaScript 渲染库
- [music21](https://web.mit.edu/music21/) — MIT 开发的音乐分析工具包
- [sounddevice](https://python-sounddevice.readthedocs.io/) — PortAudio 的 Python 绑定
- 以及 **Yamaha DX7** — FM 合成的黄金标准

---

> **Music Workshop** — 让每个人都能用键盘创作音乐 🎵
#   M u s i c - W o r k s h o p  
 