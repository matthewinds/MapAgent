# MapAgent：面向地理空间推理的动态地图工具集成分层智能体
> 中文翻译版。正式引用请以英文原文为准。

---

## 对应原文第 1 页

Findings of the Association for Computational Linguistics: EACL 2026，第 1296–1322 页
2026 年 3 月 24-29 日 ©2026 Association for Computational Linguistics
MapAgent：一种用于地理空间推理的分层智能体，具有动态
地图工具集成
Md Hasebul Hasan1,2 Mahir Labib Dihan1 Tanzima Hashem1
Mohammed Eunus Ali3 Md Rizwan Parvez4
1孟加拉国工程技术大学（BUET）
2德克萨斯大学阿灵顿分校 3莫纳什大学信息技术学院
4卡塔尔计算研究所（QCRI）
{hasebulhasan97, mahirlabibdihan}@gmail.com，
tanzimahashem@cse.buet.ac.bd, eunus.ali@monash.edu, mparvez@hbku.edu.qa
智能体式 AI（Agentic AI）通过支持复杂推理和工具使用，显著扩展了大语言模型（LLM）的能力。然而，大多数现有框架是针对数学、编程或网页自动化等领域定制的，在需要空间推理、多跳规划和实时地图交互的地理空间任务上表现不足。为应对这些挑战，我们提出了 MapAgent，这是一种分层多智能体即插即用框架，具有定制化工具集和智能体式脚手架，用于地图集成的地理空间推理。与现有扁平化基于智能体的方法不同——这些方法统一对待工具，在处理相似但细微不同的地理空间 API 时常常使 LLM 不堪重负——MapAgent 将规划与执行解耦。高层规划器将复杂查询分解为子目标，并将其路由到专门模块。对于工具密集型模块——例如基于地图的服务——我们随后设计了一个专用地图工具智能体，它能够自适应地并行高效编排相关 API，以有效获取与查询相关的地理空间数据，而更简单的模块（例如解决方案生成或答案提取）则无需额外的智能体开销即可运行。这种分层设计降低了认知负荷，提高了工具选择准确性，并实现了相似 API 之间的精确协调。我们在四个多样化的地理空间基准上评估 MapAgent——MapEval-Textual、MapEval-API、MapEval-Visual 和 MapQA——并展示了相对于最先进的工具增强和智能体式基线方法的显著提升。我们在匿名仓库中开源了我们的框架。
1 引言
智能体式大语言模型（LLM）通过支持复杂推理、子目标分解和动态工具使用，显著扩展了 AI 系统的范围（Yao et al., 2023; Kim et al., 2024; Du et al., 2024）。尽管取得了这些进
ReAct
LLMCompilerChameleonOctotoolsMapAgent
40
50
60
70
4 个任务上的平均准确率（%）
41.229
47.742
54.094
59.208
67.399
图 1：4 个地理空间基准上的性能比较。MapAgent 显著优于其他方法，并达到了最先进（SOTA）性能。
展，大多数现有框架主要关注数学（Lu et al., 2023, 2025）、软件工程（Jimenez et al., 2023）和网页自动化（Qin et al., 2023; Du et al., 2024）等领域，而它们在地理空间推理中的应用——这是一种无处不在的能力，可通过自然语言指令实现日常任务自动化，尤其是在需要与地图服务等专用工具交互的场景中——仍然有限。这包括路线规划、基于位置的决策、空间比较，以及寻找满足用户约束的附近兴趣点（例如餐厅、加油站或 EV 充电点）等任务。
与其他推理问题相比，地理空间任务提出了独特的挑战。该领域中的查询通常需要多跳规划、动态空间 grounding，以及跨多个外部 API 的协调，这些 API 具有重叠但细微不同的能力。例如，解决诸如“找到从家到办公室、并在高评分咖啡店停留的最短路线”或“规划一次从旧金山到优胜美地的三日公路旅行”
1296

---

## 对应原文第 2 页

迪拜购物中心附近哪家餐厅评分最高？
查询
响应
The GrillShack
解决方案生成器
答案生成器
视觉地点识别器
地图服务
外层 内层
图像
选定模块
仅用于视觉查询
序列器
地图工具智能体（Map-Tool Agent）
附近行程
路线
地点信息
地图服务工具集合
规划智能体（Planner Agent）
模块清单
图2：MapAgent概览。给定用户查询（可选附带图像），规划智能体（Planner Agent）利用可用的模块清单将其分解为子任务，并为每个子任务选择合适的模块。对于工具密集型模块，由专用智能体（例如地图工具智能体（Map-Tool Agent））自适应地管理与相关工具的交互。
“沿途在风景优美的城镇和徒步点过夜”涉及串联以下服务：附近地点搜索、距离估计、POI（兴趣点）检索、时间调度和实时过滤。尽管这些服务处理的是高度相关的地理空间功能，但可用的地图API在各自的模式、约束和宝贵功能上各不相同，使得有效集成它们并非易事。智能体不仅必须编排多个工具，还必须对检索到的数据进行组合和推理，以产生及时、连贯且保持地理空间一致性的响应。
然而，当前的智能体系统并非为此场景而设计。大多数即插即用的工具使用型智能体采用扁平执行架构，将工具视为通用、可互换的黑箱。这在地理空间推理背景下导致两个主要局限：(i) 工具膨胀：现有系统通常捆绑互不相同的工具——每种各一个——而未考虑地图服务中存在的细粒度功能差异。随着地理空间API的激增（例如，距离、邻近度、方向、路线规划、附近搜索、地点详情、时间线），智能体在规划和执行中面临组合负担，增加了决策复杂度并降低了整体有效性。(ii) 工具能力不足：集成到现有智能体中的工具通常是原始的（基于单一API）和通用的（例如，图像描述、表格查找、代码生成或网络搜索），并非为Google Maps等真实世界地图服务所需的丰富混合模式（并行和顺序）交互而设计。虽然某些API调用——例如计算距离和检索地点详情——可以并行执行，但许多任务需要紧密协调的顺序步骤，例如仅对先前附近搜索中识别出的地点获取详细信息。
为应对这些挑战，我们提出MapAgent，一个为地图集成地理空间推理设计的分层即插即用多智能体框架。首先，为克服工具能力不足的问题，我们设计了一组四个异构地图工具，每个工具由一个或多个原始API组成，专门用于执行关键地理空间操作。这些工具封装了常见的空间功能——例如附近搜索、路线规划和地点详情检索——并构建为支持并行和顺序执行流程。通过将底层原始API调用抽象为更高层的工具接口，MapAgent能够稳健地处理混合模式推理：例如，在顺序流水线中检索通过附近搜索找到的候选地点的详情，同时并行计算备选路线。这种结构化编排支持真实世界空间任务所需的复杂、以地图为中心的推理模式。
其次，为缓解工具膨胀问题，MapAgent采用分层架构
1297

---

## 对应原文第 3 页

方法 并行 组合式 分层 即插即用
工具调用 推理 或 Map-tools
ReAct (Yao et al., 2023) ✗ ✗ ✗ ✗
LLMCompiler (Kim et al., 2024) ✓ ✗ ✗ ✗
Octotools (Lu et al., 2025) ✓ ✓ ✗ ✓
Chameleon (Lu et al., 2023) ✗ ✓ ✗ ✓
Anytool (Du et al., 2024) ✗ ✗ ✓ ✗
MapAgent (Ours) ✓ ✓ ✓ ✓
表 1：在面向地图集成地理空间推理的背景下，不同工具调用框架的功能比较。
其将高层任务规划与低层工具执行解耦。一个顶层规划器智能体（planner agent）将复杂的自然语言查询分解为结构化子目标，并将它们路由到适当的工具工作流。对于工具密集型子目标——例如涉及地图服务的子目标——我们引入一个专用的地图工具智能体（map-tool agent），它自适应地管理与多个地图工具的交互，在适当的时候发起并行 API 调用，并在需要时协调顺序工作流。相比之下，轻量级任务——例如答案格式化或偏好综合——则直接处理，不增加额外的智能体开销。
我们在四个多样化的地理空间推理基准上评估 MapAgent——MapQA、MapEval-Textual、MapEval-Visual 和 MapEval-API——每个基准都呈现出不同的挑战，包括文本上下文、多模态输入和仅查询设置。MapAgent 使用开放权重和闭源骨干 LLM 构建，在所有基准上始终优于此前的 state-of-the-art 智能体式和工具增强型 LLM 框架。使用 GPT-3.5-Turbo 时，它在 MapEval-API 和 MapEval-Textual 数据集上均实现了 10% 的提升，并在 MapQA 数据集上相较于强基线 OctoTools (Lu et al., 2025) 实现了 11.22% 的提升。此外，在使用 GPT-4o 时，MapAgent 在 MapEval-Visual 数据集上相较于同一基线实现了 4.41% 的提升。总体而言，在需要多跳规划、空间推理和动态工具使用的地理空间任务中，MapAgent 相较于最强基线 OctoTools 平均提升了 8.2%。我们的消融、定性和细粒度分析进一步为 MapAgent 的有效性提供了更多见解。
2 相关工作
使用 LLM 的组合式推理。解决复杂的多步问题通常涉及将任务分解为可管理的子问题 (Perez et al., 2020; Khot et al., 2023)。基于提示的方法，如 Chain-of-Thought (Wei et al., 2022)、Least-to-Most (Zhou et al., 2023)、ReAct (Yao et al., 2023)、Pearl (Sun et al., 2024)、Forest-of-Thought (Bi et al., 2024) 和 rStar-Math (Guan et al., 2025)，提升了 LLM 进行顺序推理的能力。其他方法从自然语言合成结构化程序（例如 LLM Compiler (Kim et al., 2024)）或编排模块化工具（例如 Chameleon (Lu et al., 2023)、OctoTools (Lu et al., 2025)）。尽管这些系统有效，但它们通常假设模块清单是扁平的或静态的，并且难以处理在模式或功能上存在细微差异的工具变体。相比之下，MapAgent 利用分层规划和动态模块选择，以支持在重叠但异构的 API 上进行即插即用协调，尤其是在地理空间领域。
使用语言模型进行地理空间推理。地理空间问答已通过基于规则和模板驱动的系统进行研究，这些系统将自然语言转换为对静态数据库的结构化查询（例如 PostGIS、DBpedia (Auer et al., 2007)、YAGO (Suchanek et al., 2007)、Freebase (Bollacker et al., 2007)、OSM）。值得注意的例子包括基于 GeoSPARQL 的系统 (Car et al., 2022) 以及诸如 GeoQuestions1089 (Kefalidis et al., 2023) 和 YAGO2geo (Karalis et al., 2019) 等数据集。这些方法精确但缺乏灵活性，受限于其对静态模式和查询语法的依赖。
近期工作探索了 LLM 的内在地理知识（例如 GPT4GEO (Roberts et al., 2023)、(Mai et al., 2024)）或其直接回答地图相关查询的能力（例如 MapQA (Li et al., 2025)、MapEval (Dihan et al., 2025b,a)）。尽管这些模型前景可观，但它们缺乏整合外部工具或协调多 API 工作流的机制。MapAgent 建立在这一研究方向之上。
1298

---

## 对应原文第 4 页

通过引入一个多智能体、工具增强的框架，该框架能够跨模态（包括文本、视觉和 API 输入）动态协调地理空间模块，从而为现实世界中基于地图的任务提供增强的推理能力。
3 方法
我们提出 MapAgent，一个用于地图集成地理空间推理的分层即插即用多智能体框架。MapAgent 通过一个结构化的两层脚手架解决了当前智能体系统中的两个核心局限——工具能力不足（tool incapability）和工具膨胀（tool inflation），该脚手架清晰地将推理、规划和工具执行分离。
3.1 概述
我们介绍 MapAgent，一个分层多智能体框架，用于通过真实世界地图服务解决复杂的地理空间推理任务。真实世界的查询通常需要串联空间操作、查询外部 API 并整合地理证据——这些能力是单次提示（single-shot prompting）所缺乏的。为解决这一问题，MapAgent 通过分层协调编排的专用智能体，实现结构化规划、地图工具组合和空间推理。
在 MapAgent 中，顶层规划智能体 P 首先将用户查询 x 分解为子目标，从而实现模块化执行和可解释推理。这些子目标由专用功能模块 M 处理，它们将过滤或聚合等任务委托给专门的组件。图 1 展示了 MapAgent 的概览。
地理空间子目标被路由到 Map-Tool Agent Mmap，它组合了四个核心工具——Nearby、PlaceInfo、Route 和 Trip——每个工具都构建在真实世界的 Google Map API 之上，以支持空间搜索、详情检索和路线规划。这种模块化设计使 MapAgent 能够通过在基于工具的工作流上进行动态规划，解决复杂的多跳空间查询。我们在 3.2 节描述架构，3.3 节描述规划智能体和模块，3.4 节描述地图工具。
3.2 脚手架架构（层次结构）
MapAgent 包含两个概念层：
规划层（顶层）：规划智能体将输入 x 分解为一系列语义连贯的子目标 [g1,...,gn]，并根据结构化清单（在表 10 中讨论）将每个 gi 路由到功能模块或工具链。
执行层（底层）：该层管理模块特定的执行逻辑。它包括轻量级模块（例如，排序、格式化）和一个专门的 Map-Service Module，后者集成了一个专用的 Map-Tool Agent，负责使用一组精选的地图工具执行地理空间任务。
3.3 模块清单与规划智能体
规划智能体 P（基于 LLM 或 VLLM）接收输入 x、可用模块清单 M 以执行子目标，并输出结构化执行计划 π=[(g1,m1),...,(gn,mn)]，其中每个 gi 是分配给模块 mi ∈ M 的子目标。模块清单 M 包含若干任务特定模块：
Visual Place Recognizer：给定一张图像地图快照，使用相应的 VLLM，该模块提取图像中的中心地理位置（名称）并估计图像覆盖的地理范围（近似半径）。
Sequencer：该模块负责组织和结构化来自前述模块的响应。它使用 LLM 将非结构化信息整理为逻辑序列。
Solution Generator：该模块使用相应的 LLM 或 VLM 综合出对用户查询的最终答案。它接收结构化信息并生成全面的响应。
Answer Generator：该模块专注于细化和验证由 Solution Generator 生成的答案。它提取预测答案并检查其一致性。
Map-Service Module：一个由 Map-Tool Agent 管理的工具密集型模块，用于处理核心的 Map-tool 交互。
3.4 Map-Service Module：Map-Tool Agent 与工具设计
Map-Tool Agent Mmap 接收查询 x，以及对于多模态查询由 Visual Place Recognizer 推断的可选地点名称和半径。然后，它自适应地与一套地理空间工具交互，这些工具旨在从底层地图服务（例如，Google Maps）获取必要的时空数据。
我们设计了四个异构的 MapTools，每个工具由一个或多个来自 Google Map 的原始 API（例如，directions、place info）组成，以支持
1299

---

## 对应原文第 5 页

LLM
MapEval-API
Method Overall Place Info Nearby Routing Trip Unanswerable
GPT-3.5-Turbo
ReAct 27.33 39.06 22.89 33.33 19.40 15.00
LLMCompiler 44.75 53.13 51.80 48.48 37.10 0.00
Chameleon 50.45 54.54 54.10 52.00 43.07 5.00
Octotools 56.27 76.56 62.65 56.06 40.30 5.00
MapAgent 66.31 88.24 77.05 68.18 49.23 20.00
Qwen-2.5-72B
ReAct 41.56 55.44 38.25 42.40 32.75 0.00
LLMCompiler 49.63 59.25 55.29 51.23 40.77 0.00
Chameleon 52.70 61.30 60.29 55.77 46.55 10.00
Octotools 59.40 80.95 71.08 59.09 42.42 0.00
MapAgent 70.94 89.40 82.85 69.76 54.54 25.00
表 2：不同方法和骨干模型在 MapEval-API 数据集上的准确率（%）。
LLM
MapEval-Textual
Method Overall Place Info Nearby Routing Trip Unanswerable
GPT-3.5-Turbo
Base Model 37.67 26.56 53.01 48.48 28.36 5.00
ReAct 42.25 42.90 48.18 50.67 35.34 0.00
LLMCompiler 49.23 58.44 56.98 53.33 40.81 0.00
Chameleon 56.83 60.77 62.50 57.20 47.38 5.00
Octotools 62.78 84.22 68.92 61.67 44.33 5.00
MapAgent 72.94 90.06 82.76 73.23 54.15 20.00
Qwen-2.5-72B
Base Model 57.00 62.50 71.08 63.64 41.79 10.00
ReAct 58.44 64.44 68.25 56.80 46.28 5.00
LLMCompiler 62.58 74.40 75.38 64.22 48.32 5.00
Chameleon 65.75 76.40 72.54 70.60 52.26 10.00
Octotools 70.25 85.55 77.22 67.20 53.30 10.00
MapAgent 76.24 94.20 84.75 74.80 59.20 20.00
表 3：不同方法和骨干模型在 MapEval-Textual 数据集上的准确率（%）。
essential geospatial operations:
Trip Tool：检索位置信息
以及它们之间的旅行路线。结合了
Place Details 和 Directions API，以获取地点
元数据和逐步路线指引。
Route Tool：使用 Directions API 获取两点之间的路线信息，
包括距离、预计时间和导航步骤。
Nearby Tool：使用 Nearby Search API 识别指定区域内的兴趣点。
返回地点名称、评分和其他元数据。
PlaceInfo Tool：使用 Place Details API 检索给定地点的详细信息，
包括地址、营业时间、联系信息和评论。
4 实验设置
4.1 数据集
我们在四个基准上评估了 MapAgent，涵盖
两种模态，如表 4 所示。这些
基准涵盖了广泛的复杂地理空间推理任务，
包括长上下文推理、API 交互、视觉地图分析、
数值计算和多步推理。
其中三个基准来自 MapEval（Dihan et al.,
2025b）：
Dataset # Tasks Modality
MapEval-Textual 300 Text
MapEval-API 300 Text
MapEval-Visual 400 Vision
MapQA 3154 Text
表 4：数据集概览：统计和模态
MapEval-Textual：给定一个用户查询，并附带描述地图位置、POI、
路线、导航细节、旅行距离/时间和用户生成内容（如评分/评论）的长文本上下文，
任务是基于该上下文回答查询。
MapEval-API：给定一个用户查询并可访问
基于地图的 API，任务是回答查询
1300

---

## 对应原文第 6 页

VLM
MapEval-Visual
方法 总体 地点 信息 附近 路线规划 计数 无法回答
GPT-4o
Base Model 58.90 76.86 57.78 50.00 47.73 40.00
ReAct 58.50 78.28 58.24 52.29 53.11 0.00
LLMCompiler 61.88 81.29 60.80 54.42 55.22 0.00
Chameleon 62.51 82.44 62.77 55.67 57.18 5.00
Octotools 64.54 84.20 64.53 53.44 61.36 5.00
MapAgent 68.95 88.64 63.54 62.50 63.63 25.00
Qwen-2.5-VL-72B
Base Model 60.35 76.86 54.44 43.04 52.33 60.00
ReAct 59.18 74.54 54.40 56.40 55.40 10.00
LLMCompiler 64.28 82.50 61.80 58.88 59.80 10.00
Chameleon 66.40 83.46 64.32 59.30 62.35 15.00
Octotools 69.50 88.78 66.48 63.22 64.28 20.00
MapAgent 72.30 89.45 66.25 67.50 66.50 40.00
表 5：不同方法和骨干模型在 MapEval-Textual 数据集上的准确率（%）。
基于通过 API 检索到的结构化数据。
MapEval-Visual：给定一个用户查询和一张数字地图快照，其中展示了空间布局、路线、地标、OCR 文本（例如评分）以及符号元素（例如图标或标志），任务是基于视觉上下文回答该查询。
MapQA（Li et al., 2025）：一个地理空间问答基准，使用 SQL 查询模板从 OpenStreetMap 构建。它包含覆盖九种推理类型（例如邻域推断、空间邻近性、类型分类）的问答对，并以真实世界地理实体几何为基础。
4.2 基线（Baseline）与指标（Metric）
MapAgent 是一个多智能体组合推理框架。因此，我们将其性能与智能体框架进行比较，例如 ReAct（Yao et al., 2023）和 LLMCompiler（Kim et al., 2024），以及与组合推理框架进行比较，例如 Chameleon（Lu et al., 2023）和 OctoTool（Lu et al., 2025）。对于 MapEval-API、MapEval-Textual 和 MapQA 数据集，我们使用 GPT-3.5-Turbo（?）和 Qwen-2.5-72b（?）。对于 MapEval-Visual 数据集，我们使用通过 vLLM 提供的模型，具体为 GPT-4o（?）和 Qwen-2.5-VL-72b（?）。我们使用准确率评估模型性能，以百分比表示。
4.3 结果
对 MapAgent 框架在四个不同且具有挑战性的地图相关数据集上的评估揭示了其在准确率方面的显著进步，持续优于现有的智能体方法，并展现出无论底层语言模型骨干如何都具有稳健的性能。这些发现强调了 MapAgent 作为广泛地图查询处理任务的稳健解决方案的有效性。
跨基准的显著提升 在所有评估的数据集上，MapAgent 框架始终实现高准确率。在表 2 的 MapEval-API 数据集上，MapAgent 在由 GPT-3.5-Turbo 和 Qwen-2.5-72B 驱动时，分别实现了约 70% 和 72% 的总体准确率。类似地，在表 3 的 MapEval-Textual 数据集上，MapAgent 使用 GPT-3.5-Turbo 达到 72.94% 的准确率，使用 Qwen-2.5-72B 达到 76.24%。表 5 中的 MapEval-Visual 结果进一步强化了这一趋势，MapAgent 使用 GPT-4o 实现了最高的总体准确率——68.95%，使用 Qwen-2.5-VL-72B 为 72.30%。最后，在表 6 的 MapQA 基准上，MapAgent 使用 GPT-3.5-Turbo 实现了 55.58% 的最高总体准确率，使用 Qwen-2.5-72B 为 55.93%。
超越先前方法 MapAgent 的性能在所有评估的数据集和语言模型上持续超越其他突出方法，包括 OctoTools、Chameleon、ReAct 和 LLMCompiler——尤其是表现第二好的 OctoTools。在图 5 中，在 MapEval-API 数据集上，MapAgent 在使用 GPT-3.5-Turbo 和 Qwen-2.5-72B 时，分别比 OctoTools 显示出约 10% 和 11.54% 的准确率提升。对于 MapQA 基准，MapAgent 使用 GPT-3.5-Turbo 比 OctoTools 高出约 11.22%，使用 Qwen-2.5-72B 高出 9%。最后，在 MapEval-Textual 数据集上，MapAgent 的准确率
1301

---

## 对应原文第 7 页

LLM
MapQA
方法 总体 类型 1 类型 2 类型 3 类型 4 类型 5 类型 6 类型 7 类型 8 类型 9
GPT-3.5-Turbo
Base Model 24.35 32.04 7.43 5.98 50.56 7.22 31.44 18.34 10.14 56.04
ReAct 20.88 34.02 7.80 5.44 58.02 6.02 30.13 12.14 9.88 24.44
LLMCompiler23.99 36.07 8.09 6.29 67.02 7.28 31.32 14.76 14.24 30.88
Chameleon 38.11 47.52 17.59 20.77 73.14 15.52 40.12 14.28 43.68 70.40
Octotools 44.74 50.00 20.40 22.00 90.67 18.52 43.78 41.20 48.24 67.83
MapAgent 55.58 56.05 25.80 22.48 83.36 25.68 71.04 54.18 71.20 90.40
Qwen-2.5-72B
Base Model 23.51 29.60 8.40 7.20 48.00 7.60 30.00 17.20 9.20 54.40
ReAct 21.69 30.80 9.20 7.60 51.60 9.40 32.80 16.40 8.60 28.80
LLMCompiler25.60 38.40 9.20 8.00 62.40 11.60 33.20 17.60 18.40 31.60
Chameleon 40.00 51.20 27.60 23.20 68.80 22.40 38.40 20.40 38.80 68.40
Octotools 46.18 54.39 30.91 25.80 85.67 24.44 41.60 38.20 43.24 71.33
MapAgent 55.93 57.20 29.60 34.00 81.20 34.56 73.60 39.20 68.00 86.00
表 6：不同方法和骨干模型在 MapQA 数据集上的准确率（%）。
配置 Google Map API我们的 MapTools分层架构准确率（%）下降（%）
原始 API（扁平） ✓ ✗ ✗ 39.37 49.00
扁平 + MapTools ✓ ✓ ✗ 56.39 27.18
MapAgent（我们的） ✓ ✓ ✓ 77.44 -
表 7：查询求解准确率的消融研究。我们将完整的 MapAgent 与使用和不使用所提出的 MapTools 的扁平化架构进行比较。
在 GPT-3.5-Turbo 和 Qwen-2.5-72B 上，比 OctoTools 分别高出近 10% 和 6%。在 MapEval-Visual 评估中，MapAgent 在 GPT-4o 上比 OctoTools 高出约 4.41%，在 Qwen-2.5-VL-72B 上高出 2.8%。
骨干无关 MapAgent 框架的一个关键优势是其在不同的语言模型骨干上具有一致的高性能。在 MapEval-API 和 MapEval-Textual 数据集上评估时，MapAgent 在 GPT-3.5-Turbo 和 Qwen-2.5-72B 模型上都表现出更高的准确率。这在 MapEval-Visual 数据集中进一步得到体现，MapAgent 在 GPT-4o 和 Qwen-2.5-VL-72B 视觉语言模型上都取得了最高准确率。在不同 LLM 和 VLM 上一致的最高水平结果凸显了 MapAgent 的鲁棒性和适应性，表明其有效性并不依赖于任何特定的模型架构。
5 消融研究：MapTools 和分层架构
为了评估我们提出的 MapTools 和分层架构的单独影响，我们进行了一项消融研究，分析不同配置下的查询求解准确率。为了确保公平且计算高效的比较，本研究在评估数据的分层子集上进行，该子集由从四个数据集中各随机抽样的 50 个数据点组成（共 200 个样本）。因此，由于样本量较小，这里报告的绝对准确率与主要结果不同。
我们评估了三种设置：（1）完整系统；（2）使用 MapTools 的扁平化单层架构；（3）将我们的专用工具替换为直接 Google Map API 调用的扁平化架构。结果总结在表 7 中。
如表所示，当同时使用我们自定义开发的工具和分层架构时，该子集上的求解准确率达到 77.44%。然而，移除分层架构会导致性能下降 27.18%，准确率降至 56.39%。此外，移除 MapTools（在扁平架构中仅依赖原始 API）会导致额外的性能下降 22%，最终准确率降至 39.37%。这些结果证明了分层推理结构和 MapTools 提供的专用抽象的关键重要性。
关于说明 MapAgent 行为的定性示例，请参阅附录 E。
1302

---

## 对应原文第 8 页

数据集 Planner Agent Map-Tool Agent 总体误差(%)模块选择 工具调用 参数传递
MapEval-API 1.33 0.76 1.46 3.55
MapEval-Textual 0.67 1.02 0.93 2.62
MapQA 0.89 1.56 1.78 4.23
MapEval-Visual 2.5 0.66 1.2 4.36
表 8：MapAgent 的详细误差分析。我们报告了 Planner Agent（模块选择）和 Map-Tool Agent（工具调用与参数传递）在全部四个评估基准上贡献的具体错误率（%）。
6 成本分析
我们针对基线 Chameleon 和 Octotools，在四个关键指标上评估了 MapAgent 的计算效率：LLM API 调用频率、总 token 消耗量、Google Maps API 使用量以及端到端执行延迟。图 3 汇总了所有数据集上的平均资源消耗，表明 MapAgent 始终实现最低的成本概况。
这种效率源于系统之间根本性的架构差异。Chameleon 依赖顺序执行模型，解决单个查询需要在不同阶段进行多次不同的 LLM API 调用——包括为各个模块（例如 Nearby、Trip、Route）提取参数、解决方案规划和答案生成。这种顺序依赖关系同时加剧了 API 调用次数和整体延迟。类似地，Octotools 采用迭代式、来回往复的推理过程。虽然灵活，但这种方法本质上会产生额外的 LLM 和 Google Maps API 交互，导致更高的平均延迟。
相比之下，MapAgent 在其内部 Map-Tool Agent 中利用了并行执行框架。通过使系统能够在单次 LLM API 调用中同时执行多个工具，MapAgent 消除了为每次工具调用进行单独交互的需要。这一架构优势大幅减少了 API 调用总数和执行时间，确保在所有评估配置下实现更快、更高效的查询解析。有关成本分析细分的进一步统计细节见附录 D。
7 误差分析与挑战
为了精准定位 MapAgent 剩余的挑战，我们进行了细粒度的误差分析，考察框架各个阶段的具体错误类型。
Octotools Chameleon MapAgent
方法
0.0
2.5
5.0
7.5
10.0
12.5
15.0
17.5
20.0平均值
指标
LLM API 调用
Token（K）
Google Map API 调用
执行时间（秒）
图 3：MapAgent 与 Chameleon 和 Octotools 的总体成本分析比较。MapAgent 在全部四个指标上实现了更低的资源消耗：LLM API 调用、Token 使用量、Google Maps API 调用和执行时间。
如图 4 所示，MapAgent 在四个地理空间基准上呈现出平均错误百分比。虽然平均错误率并不显著，但 MapEval-Visual 数据集约为 4.36%，MapQA 为 4.24%，MapEval-API 为 3.55%，MapEval-Textual 为 2.62%。此外，表 8 详细列出了归因于 MapAgent 内各组件的平均错误百分比。我们的分析揭示了几个关键错误来源：
Planner Agent：虽然总体准确，但 Planner Agent 偶尔无法从其清单中选择合适的模块。我们观察到不同任务的错误率有所差异：MapEval-Textual 约为 0.67%，MapQA 为 0.89%，MapEval-API 为 1.33%，MapEval-Visual 为 2.5%。这些错误通常源于错误的组件选择或操作顺序。
Map-Tool Agent：该 agent 可能遇到两种潜在类型的错误：获取错误的工具或向这些工具传递不恰当的参数。虽然错误率并不显著，但详见表 8。
1303

---

## 对应原文第 9 页

MapEval-Textual MapEval-API MapQA MapEval-Visual
Geospatial Benchmarks
0
1
2
3
4
5Average Overall Cascade Error (%)
2.62
3.55
4.23 4.36
Figure 4: MapAgent 在四个地理空间基准上的平均总体级联误差（%）。结果表明，即使在 MapEval-Visual 等复杂任务上，该系统仍保持较低的误差传播率（< 4.5%）。
8 更广泛的影响与伦理考量
尽管 MapAgent 是为城市导航和位置发现等良性应用而设计的，但我们认识到，先进的地理空间推理系统具有两用风险（Hovy et al., 2016）。
两用关切。我们的系统处理模糊位置描述并自主执行复杂空间查询的能力，可能被滥用于监视或军事目的。那些帮助用户寻找餐厅或规划路线的相同能力，理论上也可以被改造用于追踪个人或支持瞄准系统。我们强烈反对在侵犯隐私权或助长有害应用的场景中部署该系统。
数据偏差与公平性。MapAgent 依赖商业地图 API，而这些 API 可能包含固有偏差。如果这些来源对某些街区或群体代表性不足，我们的系统可能会通过将用户引导远离记录不足的地区，无意中强化这些差距。这会造成导航不公平和信息获取不平等的风险。开发者应审查其数据源是否存在偏差，并在可能的情况下实施纠正。
隐私考量。任何地理空间推理系统的部署都应通过知情同意、数据最小化和系统能力透明化来优先保护用户隐私。用户需要了解收集了哪些信息以及他们的查询是如何被处理的。我们建议纳入隐私-by-design（privacy-by-design）原则，并让用户控制自己的数据。
我们希望通过明确回应这些关切，能够鼓励地理空间 AI 系统的负责任开发，同时将潜在危害降至最低。
9 结论
在本文中，我们提出了 MapAgent，一个为有效地理空间推理而设计的分层多智能体（multi-agent）框架。通过将规划与执行解耦，并引入具有定制工具集的专门模块——例如专用的地图工具智能体——MapAgent 解决了扁平化基于智能体的架构所面临的局限，这些架构难以应对工具过载和细粒度 API 协调问题。通过对四个具有挑战性的地理空间基准——MapEval-Textual、MapEval-API、MapEval-Visual 和 MapQA——进行全面评估，MapAgent 始终优于现有的工具增强和智能体基线，包括 Chameleon 和 OctoTools。这些结果证明了 MapAgent 在真实世界、地图集成推理任务中的有效性和泛化能力。在未来工作中，我们计划扩展该框架以支持多智能体协作（Hosain et al., 2025），并处理更广泛的多模态时空推理任务。
局限性
尽管我们提出的分层多智能体框架 MapAgent 在各种地理空间查询上相较于最先进的工具增强和智能体基线表现出显著提升，但它目前依赖一组有限的主流 Google Maps API。将框架扩展到支持更广泛的 API 和地图服务，将进一步验证其泛化性和鲁棒性。此外，尽管 MapAgent 具有即插即用（plug-and-play）架构，并有可能应用于其他领域，例如 Web 自动化和软件工程，但其在这些领域中的有效性仍有待评估。
参考文献
Sören Auer, Christian Bizer, Georgi Kobilarov, Jens Lehmann, Richard Cyganiak, and Zachary Ives. 2007. Dbpedia: A nucleus for a web of open data. In international semantic web conference, pages 722–735. Springer.
Zhenni Bi, Kai Han, Chuanjian Liu, Yehui Tang, and Yunhe Wang. 2024. Forest-of-thought: Scaling test-
1304

---

## 对应原文第 10 页

用于增强 LLM 推理的测试时计算。arXiv
e-prints，页码 arXiv–2412。
Kurt Bollacker, Robert Cook, and Patrick Tufts. 2007.
Freebase：一个结构化通用人类知识的共享数据库。In AAAI, volume 7, pages 1962–
1963。
Nicholas J Car, Timo Homburg, Matthew Perry, John
Herring, Frans Knibbe, Simon JD Cox, Joseph Abha-
yaratna, and Mathias Bonduel. 2022. Ogc geosparql-
一种用于 rdf 数据的地理查询语言。OGC Im-
plementation Standard., Open Geospatial Consor-
tium。
Mahir Labib Dihan, Mohammed Eunus Ali, and
Md Rizwan Parvez. 2025a. MapQaTor：一个用于高效标注基于地图的
QA 数据集的可扩展框架。In Proceedings of the 63rd Annual
Meeting of the Association for Computational Lin-
guistics (Volume 3: System Demonstrations), pages 1–
10, Vienna, Austria. Association for Computational
Linguistics。
Mahir Labib Dihan, Md Tanvir Hassan, Md Tanvir
Parvez, Md Hasebul Hasan, Md Almash Alam,
Muhammad Aamir Cheema, Mohammed Eunus Ali,
and Md Rizwan Parvez. 2025b. Mapeval：基础模型中基于地图的
地理空间推理评估。In Forty-second International Confer-
ence on Machine Learning。
Yu Du, Fangyun Wei, and Hongyang Zhang. 2024. Any-
tool：用于大规模 api 调用的自反思、分层智能体。In International Conference on Ma-
chine Learning, pages 11812–11829. PMLR。
Xinyu Guan, Li Lyna Zhang, Yifei Liu, Ning Shang,
Youran Sun, Yi Zhu, Fan Yang, and Mao Yang.
2025. rstar-math：小型 llm 可以通过自演化深度思考掌握数学推
理。arXiv preprint
arXiv:2501.04519。
Md Tanzib Hosain, Salman Rahman, Md Kishor Morol,
and Md Rizwan Parvez. 2025. Xolver：像
奥林匹克团队一样进行整体经验学习的多智能体
推理。arXiv preprint arXiv:2506.14234。
Dirk Hovy, Shannon L Spruit, and 1 others. 2016. 自然语言处理的
社会影响。In The
54th Annual Meeting of the Association for Compu-
tational Linguistics Proceedings of the Conference,
Vol. 2 (Short Papers). Association for Computational
Linguistics。
Carlos E Jimenez, John Yang, Alexander Wettig,
Shunyu Yao, Kexin Pei, Ofir Press, and Karthik
Narasimhan. 2023. Swe-bench：语言模型
能解决真实世界的 github 问题吗？arXiv preprint
arXiv:2310.06770。
Nikolaos Karalis, Georgios Mandilaras, and Manolis
Koubarakis. 2019. 用精确地理空间知识扩展 yago2 知识
图谱。In The
Semantic Web–ISWC 2019: 18th International Se-
mantic Web Conference, Auckland, New Zealand, Oc-
tober 26–30, 2019, Proceedings, Part II 18 , pages
181–197. Springer。
Sergios-Anestis Kefalidis, Dharmen Punjani, Eleni
Tsalapati, Konstantinos Plas, Mariangela Pollali,
Michail Mitsios, Myrto Tsokanaridou, Manolis
Koubarakis, and Pierre Maret. 2023. 使用数据集
geoquestions1089 对地理空间问答引擎进行基准
测试。In International semantic
web conference, pages 266–284. Springer。
Tushar Khot, Harsh Trivedi, Matthew Finlayson, Yao
Fu, Kyle Richardson, Peter Clark, and Ashish Sab-
harwal. 2023. 分解式提示：解决复杂任务的模块化
方法。In The Eleventh
International Conference on Learning Representa-
tions。
Sehoon Kim, Suhong Moon, Ryan Tabrizi, Nicholas
Lee, Michael W Mahoney, Kurt Keutzer, and Amir
Gholami. 2024. 用于并行函数
调用的 llm 编译器。In Forty-first International Conference on
Machine Learning。
Zekun Li, Malcolm Grossman, Mihir Kulkarni, Muhao
Chen, Yao-Yi Chiang, and 1 others. 2025. Mapqa：
基于地图数据的开放域地理空间问答。arXiv preprint arXiv:2503.07871。
Pan Lu, Bowen Chen, Sheng Liu, Rahul Thapa, Joseph
Boen, and James Zou. 2025. Octotools：一个用于复杂推理的、具有可扩展工具的智能体
框架。In ICLR 2025 Workshop on Foundation Models
in the Wild。
Pan Lu, Baolin Peng, Hao Cheng, Michel Galley, Kai-
Wei Chang, Ying Nian Wu, Song-Chun Zhu, and
Jianfeng Gao. 2023. Chameleon：使用大型语言模型的即插即用
组合式推理。Advances in Neural Information Processing Systems ,
36:43447–43478。
Gengchen Mai, Weiming Huang, Jin Sun, Suhang Song,
Deepak Mishra, Ninghao Liu, Song Gao, Tianming
Liu, Gao Cong, Yingjie Hu, Chris Cundy, Ziyuan Li,
Rui Zhu, and Ni Lao. 2024. 论基础模型用于 geoai 的机遇与
挑战（愿景论文）。ACM Trans. Spatial Algorithms Syst., 10(2)。
Md Rizwan Parvez. 2025. 证据链与证
据生成：面向上下文接地
和检索增强推理的提示。In Proceedings
of the 4th International Workshop on Knowledge-
Augmented Methods for Natural Language Process-
ing, pages 230–245, Albuquerque, New Mexico,
USA. Association for Computational Linguistics。
Ethan Perez, Patrick Lewis, Wen-tau Yih, Kyunghyun
Cho, and Douwe Kiela. 2020. 用于问答的无监督问题
分解。In Proceed-
ings of the 2020 Conference on Empirical Methods
in Natural Language Processing (EMNLP) , pages
8864–8880。
1305

---

## 对应原文第 11 页

Yujia Qin, Shihao Liang, Yining Ye, Kunlun Zhu, Lan Yan, Yaxi Lu, Yankai Lin, Xin Cong, Xiangru Tang, Bill Qian, and 1 others. 2023. Toolllm: Facilitating large language models to master 16000+ real-world apis. arXiv preprint arXiv:2307.16789.
Jonathan Roberts, Timo Lüddecke, Sowmen Das, Kai Han, and Samuel Albanie. 2023. GPT4GEO: How a language model sees the world’s geography. In NeurIPS 2023 Foundation Models for Decision Making Workshop.
Fabian M Suchanek, Gjergji Kasneci, and Gerhard Weikum. 2007. Yago: a core of semantic knowledge. In Proceedings of the 16th international conference on World Wide Web, pages 697–706.
Simeng Sun, Yang Liu, Shuohang Wang, Dan Iter, Chenguang Zhu, and Mohit Iyyer. 2024. Pearl: Prompting large language models to plan and execute actions over long documents. In Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers), pages 469–486.
Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Fei Xia, Ed Chi, Quoc V Le, Denny Zhou, and 1 others. 2022. Chain-of-thought prompting elicits reasoning in large language models. Advances in neural information processing systems, 35:24824–24837.
Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. 2023. React: Synergizing reasoning and acting in language models. In International Conference on Learning Representations (ICLR).
Denny Zhou, Nathanael Schärli, Le Hou, Jason Wei, Nathan Scales, Xuezhi Wang, Dale Schuurmans, Claire Cui, Olivier Bousquet, Quoc V Le, and Ed H. Chi. 2023. Least-to-most prompting enables complex reasoning in large language models. In The Eleventh International Conference on Learning Representations.
1306

---

## 对应原文第 12 页

## A MapAgent 如何优于 Chameleon 和 OctoTools

附录 A.1、A.2 和 A.3 展示了一个示例，其中 OctoTools 和 Chameleon 未能解决一个复杂的地理空间查询，但 MapAgent 可以。这种失败背后的主要原因是 OctoTools 和 Chameleon 将所有模块或工具卡片都放在一层中。因此，它们难以猜测用于获取信息的准确工具/模块。该示例表明，解决此查询需要查询中每个位置到另一位置的距离和旅行时间，而行程工具（trip tool）可以正确提供这些信息。然而，Chameleon 和 OctoTools 在这里都遇到了困难，并选择路线工具（route tool）来获取信息，随后缺乏所有地点之间所有路线的信息。此外，OctoTools 还遇到了另一个限制。如表 9 所示，其中显示了 OctoTools 的中间推理步骤，我们发现该框架产生了幻觉，并触发了一个带有与问题无关参数的工具，从而产生了错误信息。这些限制导致无法向后续步骤提供所有所需信息。然而，MapAgent 可以通过在 Google Map 模块中引入一个内层来有效解决这个问题。该模块与一个地图工具智能体（map-tool agent）通信，适当地触发行程工具并检索相关信息，这些信息足以让后续步骤确定解决方案。

MapEval-API
MapQA
MapEval-TextualMapEval-Visual
0
2
4
6
8
10
12准确率(%) MapAgent 相对于 OctoTools 的增益
10.00
11.54 11.22
9.00
10.00
6.00
4.41
2.80
GPT-3.5-Turbo
Qwen-2.5-72B
GPT-4o
Qwen-2.5-VL-72B

图 5：MapAgent 相对于 OctoTools 在各种基准测试上的准确率提升。

### A.1 Octotools 输出 绿色：正确答案 红色：错误答案

• PID：19
• 查询：我在 Rydges Wellington。从我的当前位置出发，我将首先前往 Kelburn Park，然后前往 Victoria University of Wellington，最后返回我的当前位置。所有行程都将使用我自己的汽车完成。整个旅程需要多长时间？
• 选项：A.11 分钟 B.10 分钟 C.12 分钟 D.9 分钟
• 正确答案：B
• 推理步骤：表 9 显示了 OctoTools 的推理步骤及其在每个步骤中执行的工具。在表中，红色高亮表示幻觉，橙色高亮表示 OctoTools 在执行后试图获取的不正确信息。我们观察到，首次调用 Route Tool 时，使用相同的起点和终点，导致信息检索不准确。此外，表第 2 行至第 5 行中显示的后续九次调用表明存在幻觉，并使用了与问题无关的参数，揭示出缺乏正确的工具调用。尽管存在一个能够在单次调用中提供所有相关信息的行程工具，但它没有被正确执行。
• Octotools 最终输出：为了确定从 Rydges Wellington 出发并返回 Rydges Wellington、途中停靠 Kelburn Park 和 Victoria University of Wellington 的往返总旅行时间，采取了以下步骤：
步骤 1：分析查询 查询指定了一次往返行程：1. 从 **Rydges Wellington** 出发。2. 访问 **Kelburn Park**。3. 前往 **Victoria University of Wellington**。4. 返回 **Rydges Wellington**。交通方式为驾车。
步骤 2：使用 Route Tool 使用 **Route Tool** 计算指定路线的总驾车时间。该工具提供了以下结果：- **总路线距离**：1.9 公里。- **总驾车时间**：9 分钟。
步骤 3：验证路线详情 路线详情确认驾车时间包括行程的所有路段：- Rydges Wellington → Kelburn Park。- Kelburn Park → Victoria University of Wellington。- Victoria University of Wellington → Rydges Wellington。

1307

---

## 对应原文第 13 页

结论：整个行程的总驾驶时间为 **9 分钟**。
**最终答案：D. 9 mins**
A.2 Chameleon 输出 绿色：正确答案 红色：错误答案
• PID：19
• 查询：我在 Rydges Wellington。从我的当前位置出发，我将首先前往 Kelburn Park，随后前往 Victoria University of Wellington，最后返回我的当前位置。所有出行都将使用我自己的汽车完成。整个行程需要多长时间？
• 选项：A.11 mins B.10 mins C.12 mins D.9 mins
• 正确答案：B
• Planner 选择的模块：Route、solution_generator、answer_generator
• Route 模块收集的信息：
从 Rydges Wellington, Wellington 6011, New Zealand 到 Victoria University of Wellington, Wellington 6012, New Zealand 共有 1 条路线。路线信息如下：
路线 1：（经由）Parkvale Rd（7.6 km，20 mins）。
详细步骤如下：
沿 Featherston St 向西南方向行驶，朝 Whitmore St 前进（35 m，1 min）
在第 1 个交叉路口右转，进入 Whitmore St（0.2 km，1 min）
继续进入 Bowen St（0.8 km，2 mins）
左转进入 Tinakori Rd（指示牌指向 Karori/Botanic Garden）（0.2 km，1 min）
继续进入 Glenmore St（1.6 km，3 mins）
在环岛处，从第 1 个出口驶出并继续沿 Glenmore St 行驶（0.2 km，1 min）
继续进入 Karori Tunnel（0.1 km，1 min）
继续进入 Chaytor St（0.9 km，2 mins）
继续进入 Karori Rd（1.2 km，2 mins）
右转进入 Parkvale Rd（1.1 km，2 mins）
右转以继续沿 Parkvale Rd 行驶（0.3 km，1 min）
右转以继续沿 Parkvale Rd 行驶（1.1 km，5 mins）
• Solution Generator 生成的解决方案：
所提供的信息似乎存在不匹配。你给出的详细路线是 Rydges Wellington 与 Victoria University of Wellington 之间的行程，耗时约 20 分钟。你没有提供 Rydges Wellington 与 Kelburn Park 之间那一段的详细路线或旅行时间，也没有提供从 Victoria University of Wellington 经 Kelburn Park 返回 Rydges Wellington 的返程信息。仅根据你刚刚提供的 Rydges 到 Victoria University 的 20 分钟旅行时间（路线 1），在不知道其他路段旅行时间的情况下，我们无法准确回答涉及 Kelburn Park 的整个行程问题。
然而，如果我们忽略你提到的先前旅行时间，并假设问题暗示的是从 Rydges 到 Victoria University 再返回的直接行程，且每个方向都使用 20 分钟路线，那么总计将是 20 分钟 + 20 分钟 = 40 分钟。
这与提供的选项不一致。
所以，答案应为 E。
• Answer Generator 模块输出：
无法回答该问题
A.3 MapAgent 输出 绿色：正确答案 红色：错误答案
• PID：19
• 查询：我在 Rydges Wellington。从我的当前位置出发，我将首先前往 Kelburn Park，随后前往 Victoria University of Wellington，最后返回我的当前位置。所有出行都将使用我自己的汽车完成。整个行程需要多长时间？
• 选项：A.11 mins B.10 mins C.12 mins D.9 mins
• 正确答案：B
• Planner Agent 选择的模块：
map_service、solution_generator、answer_generator
• Google_Maps 模块收集的信息：
所有位置信息：
Rydges Wellington
名称：Rydges Wellington
地址：75 Featherston Street, Pipitea, Wellington 6011, New Zealand
1308

---

## 对应原文第 14 页

评分：4.2
类型：住宿、兴趣点、机构
当前是否营业：是
工作日营业时间：
- 星期一：24 小时营业
- 星期二：24 小时营业
- 星期三：24 小时营业
- 星期四：24 小时营业
- 星期五：24 小时营业
- 星期六：24 小时营业
- 星期日：24 小时营业
Kelburn Park
名称：Kelburn Park
地址：Salamanca Road, Kelburn, Wellington 6012, New Zealand
评分：4.4
类型：公园、旅游景点、兴趣点、机构
当前是否营业：是
工作日营业时间：
- 星期一：24 小时营业
- 星期二：24 小时营业
- 星期三：24 小时营业
- 星期四：24 小时营业
- 星期五：24 小时营业
- 星期六：24 小时营业
- 星期日：24 小时营业
Victoria University of Wellington
名称：Victoria University of Wellington
地址：Kelburn Parade, Kelburn, Wellington 6012, New Zealand
评分：4.3
类型：大学、兴趣点、机构
当前是否营业：N/A
工作日营业时间：
- 未知
从 Rydges Wellington 到 Kelburn Park 的旅行时间（距离）为 5 分钟（1.6 km）
从 Rydges Wellington 到 Victoria University of Wellington 的旅行时间（距离）为 1 分钟（1 m）
从 Kelburn Park 到 Rydges Wellington 的旅行时间（距离）为 4 分钟（1.4 km）
从 Kelburn Park 到 Victoria University of Wellington 的旅行时间（距离）为 4 分钟（1.4 km）
从 Victoria University of Wellington 到 Rydges Wellington 的旅行时间（距离）为 1 分钟（1 m）
从 Victoria University of Wellington 到 Kelburn Park 的旅行时间（距离）为 5 分钟（1.6 km）
• 由 Solution Generator 模块生成的解决方案：要计算整个行程的总时间，我们需要考虑从 Rydges Wellington 到 Kelburn Park 的旅行时间，然后是从 Kelburn Park 到 Victoria University of Wellington 的旅行时间，最后是从 Victoria University of Wellington 返回 Rydges Wellington 的返程时间。
从 Rydges Wellington 到 Kelburn Park 的旅行时间是 5 分钟。从 Kelburn Park 到 Victoria University of Wellington 的旅行时间是 4 分钟。从 Victoria University of Wellington 返回 Rydges Wellington 的返程时间是 1 分钟。
将这些时间相加，整个行程的总时间是 5 + 4 + 1 = 10 分钟。
所以，答案是 10 分钟。最可能的选项是“答案是 B”
• 由 Answer Generator 模块生成的答案：B. 10 mins
B MapAgent 中的配置
B.1 Map-Tool Agent
Map-Tool Agent 的提示词
你是一个 agent，旨在理解用户问题并使用特定工具检索相关信息。当用户提出问题时，你的任务是从可用列表（Trip Tool、Route Tool、Nearby 和 PlaceInfo）中识别出最能回答该查询的合适工具。然后你将使用该工具获取信息，并将检索到的数据提供给用户。
你不应直接回答问题；你的角色仅仅是使用指定工具检索必要信息。例如，如果你认为需要使用多个工具，可以并行使用它们。
1309

---

## 对应原文第 15 页

B.2 解决方案生成器（MapEval-API）
解决方案生成器的提示词
给定问题（以及上下文），从选项 ["A"、"B"、"C"、"D"] 中选择答案。你应当给出简洁且分步的解答。最后，以 "the answer is [ANSWER]" 的格式得出结论，其中 [ANSWER] 是选项 ["A"、"B"、"C"、"D"] 中的一个。例如，"the answer is A"、"the answer is B"、"the answer is C" 或 "the answer is D"。如果答案不在选项中，则声明为 Unanswerable。
# 示例 1
问题：Multiplan Center 的地址是什么？
选项：(A) 69, 71 New Elephant Rd, Dhaka 1205, Bangladesh (B) 38/1/C BC DAS Street Lalbagh (C) Polashi,BUET (D) Central Road, USA
元数据：{"skill":"Fetch context from corresponding google map api and based on the context answer the question"}
Google Maps 响应：
名称：Multiplan Center
地址：69, 71 New Elephant Rd, Dhaka 1205, Bangladesh
评分：4.4
类型：point_of_interest, establishment
当前是否营业：False
工作日营业时间：
- 星期一：10:00AM–8:00PM
- 星期二：Closed
- 星期三：10:00AM–8:00PM
- 星期四：10:00AM–8:00PM
- 星期五：10:00AM–8:00PM
- 星期六：10:00AM–8:00PM
- 星期日：10:00AM–8:00PM
解答：如果你查看上下文并搜索，那么在到达之后，Multiplan Center 的地址是 69, 71 New Elephant Rd, Dhaka 1205, Bangladesh。因此，the answer is B。
.... <另外 4 个示例> ....
现在回答以下问题。
# 问题：{question}
B.3 视觉地点识别器
视觉地点识别器的提示词
我将为你提供一张图像。你必须确定图像内的精确中心位置，并通过从中心预测一个半径来预测图像的边界。你的返回格式应为：中心位置名称后跟一个空格，然后是半径。在此基础上，仅提供一个完整地址，采用单一、一致的格式，后跟一个空格和一个半径。不要在地址之前或之后包含任何多余文本。
C 详细工具参数
以下部分概述了 Map Service 模块所使用的工具，这些工具由 map-tool agent 检索得到。每个工具都与其输入参数一起定义。
Trip Tool
current_location (str)：行程的起始位置。
visiting_places (list)：要访问的位置列表。
travel_mode (str)：出行方式，默认为 driving。
Route Tool
origin (str)：路线的起始位置。
destination (str)：路线的目的地。
travel_mode (str)：出行方式，默认为 driving。
mode (str)：用于路线的交通方式，例如 "driving"
alternatives (bool)：是否返回多条可能路线。
1310

---

## 对应原文第 16 页

Nearby Tool
query (str)：要查找的地理空间地点的搜索词。
location (str)：当前地点的名称（例如，Ibn Sina Hospital, Dhaka）。
type (str)：要搜索的地点类型，例如 "restaurant"、"cafe" 或 "hospital"。
radius (float)：用于过滤的圆形区域半径，默认为 20 公里
PlaceInfo Tool
location_address (str)：要搜索的位置的地址或名称。
D 详细成本分析
在本节中，我们提供第 6 节中所述成本分析的细粒度分解。我们将 MapAgent 与基线在四个数据集（MapEval-API、MapEval-Textual、MapEval-Visual 和 MapQA）以及四个 LLM 主干（GPT-3.5-Turbo、Qwen-2.5-72B、GPT-4o 和 Qwen-2.5-VL-72B）上进行比较。
详细结果呈现在以下表格中：
• 表 12：每次查询的平均 LLM API 调用次数。
• 表 13：平均 token 消耗量（以千为单位）。
• 表 14：每次查询的平均 Google Maps API 调用次数。
• 表 15：平均执行时间（以秒为单位）。
与总体趋势一致，MapAgent 在每个子类别中都展现出卓越的效率，验证了分层并行架构的可扩展性。
E 定性示例
E.1 MapAgent 如何回答查询
列表 1 和图 6 展示了 MapAgent 如何处理一个典型的地理空间查询。在此示例中，查询取自 trip 类别："I am currently at Planetshakers Church Melbourne City Campus. I want to drive to Carrot Tattoo Studio and then to Melbourne Lifestyle Apartments - Docklands Accommodation. How long will this take?"
最初，查询被传递给 Planner Agent，它分析查询并选择三个模块来解决它：google_maps、solution_generator 和 answer_generator。随后，google_maps 模块被执行，并尝试通过调用其 map-tool agent 和相关工具从 Google Maps 获取信息。执行随后被移交给 map-tool agent。基于查询，map-tool agent 选择 trip 工具来检索此特定问题所需的信息。trip 工具利用 Directions 和 Place Details API 来获取解决此特定查询的信息。然后 map-tool agent 将此信息返回给 google_maps 模块。Google Maps 模块随后将此信息传递给 solution_generator。基于 google_maps 获取的信息和查询本身，solution_generator 尝试用适当的解释来制定答案，并将其移交给 answer_generator。最后，在验证答案后，answer_generator 从 solution_generator 提供的解释中提取最终答案，并呈现最终输出。通过将任务分解为多个步骤，这种方法解决了 LLM 的长上下文处理限制（Parvez, 2025）。
E.2 MapAgent 如何回答带有视觉上下文的查询
列表 2、3、4、5 和图 7 展示了 MapAgent 如何处理包含视觉上下文（例如位置的快照）的地理空间查询的示例。为了解决这类问题，问题和图像由 Planner Agent 处理。Planner Agent 通常选择 Visual Place Recognizer Module、google_maps 模块、solution_generator 模块和 answer_generator 模块。Image Search 模块识别图像中的中心位置并估计其边界，通常提供距中心位置的半径。此位置信息连同原始查询一起被传递给 google_maps 模块。Google Maps 通过其 map-tool agent 和调用 Google Maps API 的工具，从其内层获取进一步的相关信息。最后，与前一个示例类似，解决方案被生成并精炼。
1311

---

## 对应原文第 17 页

解决方案生成器（Solution Generator）
答案生成器（Answer Generator）
地图服务（Map Service）
规划智能体（Planner Agent）
地图工具智能体（Map-Tool Agent）
在执行 map_service 模块时，它会连接到内层（Inner Layer）的 map-tool agent。
所有位置信息：
Planetshakers Church Melbourne City Campus
名称：
Planetshakers Church Melbourne City Campus
地址：400 City Rd, Southbank VIC 3006, Australia
评分：4.8
……
从 Planetshakers Church Melbourne City Campus 到 Carrot Tattoo Studio 的出行时间（距离）为 9 分钟（2.0 km）。从 Melbourne Lifestyle Apartments - Docklands Accommodation 到 Carrot Tattoo Studio 的出行时间（距离）为 11 分钟（2.7 km）。
Lifestyle Apartments - Docklands Accommodation 到 Carrot Tattoo Studio 为 11 分钟（2.7 km）
........

为了确定从 Planetshakers Church Melbourne City Campus 到 Carrot Tattoo Studio，然后到 Melbourne Lifestyle Apartments - Docklands Accommodation 的总出行时间，我们需要将旅程每一段的出行时间相加。
1. **从 Planetshakers Church Melbourne City Campus 到 Carrot Tattoo Studio：**
- 出行时间：9 分钟
2. **从 Carrot Tattoo Studio 到 Melbourne Lifestyle Apartments - Docklands Accommodation：**
- 出行时间：10 分钟
现在，我们将这些出行时间相加：9 分钟 + 10 分钟 = 19 分钟。因此，总出行时间为 19 分钟。
根据 solution generator 的响应，答案应为 19 Minutes，这看起来合理且正确。答案是 B. 19 Minutes
我目前在 Planetshakers Church Melbourne City Campus。我想开车去 Carrot Tattoo Studio，然后去 Melbourne Lifestyle Apartments - Docklands Accommodation。这会花多长时间？
选项：A. 18 mins  B. 19 mins  C. 20 mins  D. 21 mins
查询（Query）
序列器（Sequencer）
行程（Trip）
组织后的地理空间信息（Organized Geospatial Information）
I. 位置详情：Planetshakers Church Melbourne City Campus
名称：Planetshakers Church Melbourne City Campus
…
II. 出行时间与距离
（所有配对均为双向）：
Planetshakers Church Melbourne City Campus 到 Carrot Tattoo Studio
时间：9 mins ...
图 6：详细示例：MapAgent 如何解决一个查询，包括每个模块的输出
解决方案生成器（Solution Generator）
答案生成器（Answer Generator）
视觉地点识别器（Visual Place Recognizer）
地图服务（Map Service）
规划智能体（Planner Agent）
地图工具智能体（Map-Tool Agent）
附近（Nearby）
这张图像的中心点表示 Radmansgatan 46, 113 57 Stockholm, Sweden 的位置。从该中心点到图像边缘的半径应为 600 米。
在执行 map_service 模块时，它会连接到内层（Inner Layer）的 map-tool agent。
在位置 Radmansgatan 46, 113 57 Stockholm, Sweden 的 0.8 公里范围内有一些教堂，如下所示：
City Church（距离：0.46526450497253263 公里，评分：4.6，总评论数：94）
St. Peter's Church, Stockholm（距离：0.584886996790922 公里，评分：4.5，总评论数：42）
Adolf Fredriks Forsamling（距离：0.36249979086127565 公里，评分：4.5，总评论数：341）
根据提供的地图和 Google Maps 上下文，在地图下半部分可见的教堂是：
St. Peter's Church, Stockholm
Adolf Fredriks Forsamling
City Church
因此，正确答案是 B. Three。
B. Three。
地图下半部分可见多少座教堂？
选项：A.Five B.Two C.Four D.Three
查询（Query）
图像（Image）
图 7：详细示例：MapAgent 如何解决一个查询，包括每个模块的输出
1312

---

## 对应原文第 18 页

表 9：Octotools 的详细推理步骤
步骤 工具 子目标 命令 结果摘要
动作
步骤 1
Route
Tool
计算从 Rydges Wellington 出发，途经 Kelburn Park 和 Victoria University of Wellington，并返回 Rydges Wellington 的往返总驾车时间。
execution=tool.execute(origin="RydgesWellington",destination="RydgesWellington",waypoints=["KelburnPark","VictoriaUniversityofWellington"],mode="driving",alternatives=False)
共 1 条路线。经由 Dixon St（1.9 km，9 分钟）。详情包括逐步导航指引。
动作
步骤 2
Route
Tool
计算从 Trevi Fountain 到 Vatican Museum 使用公共交通的出行时间。
execution=tool.execute(origin="TreviFountain",destination="VaticanMuseum",mode="transit")
从 Trevi Fountain 到 Vatican Museum 共有 6 条路线，经由不同公共交通选项，时间范围为 30 至 39 分钟。
动作
步骤 3
Route
Tool
使用 Route_Tool 计算从 Kockelscheuer Ice Rink 到 Kallektuffquell 的公共交通路段出行时间。
execution=tool.execute(origin="KockelscheuerIceRink",destination="Kallektuffquell",mode="transit")
从 Kockelscheuer Ice Rink 到 Kallektuffquell 共有 6 条公共交通路线，时间范围为 1 小时 50 分钟至 2 小时 10 分钟。
动作
步骤 4
Route
Tool
计算从 Planetshakers Church Melbourne City Campus 到 Melbourne Lifestyle Apartments - Docklands Accommodation 并在 Carrot Tattoo Studio 停靠的路线总驾车时间
execution=tool.execute(origin="PlanetshakersChurchMelbourneCityCampus",destination="MelbourneLifestyleApartments-DocklandsAccommodation",waypoints=["CarrotTattooStudio"],mode="driving",alternatives=False)
从 Planetshakers Church 到 Melbourne Lifestyle Apartments（经由 Carrot Tattoo Studio）共 1 条路线（2.0 km，9 分钟），包含逐步导航指引。
动作
步骤
5-10
Route
Tool
计算从 Hotel Saltel 到 Nil Ratan Sircar Medical College and Hospital 并在 Science City - Kolkata 停靠的路线总驾车时间。
execution=tool.execute(origin="HotelSaltel",destination="NilRatanSircarMedicalCollegeandHospital",waypoints=["ScienceCity-Kolkata"],mode="driving",alternatives=False)
每一步显示从 Hotel Saltel 到 Nil Ratan Sircar Medical College（经由 Science City - Kolkata）的 1 条路线（2.8 km，7 分钟），包含逐步导航指引。
1313

---

## 对应原文第 19 页

模块 描述
Map Service 使用名为 Map-Tool Agent 的 Coordinator Agent 获取地理空间数据。
检索地点详情、路线、附近位置及其他地图相关信息。
Visual Place
Recognizer 使用 VLLM 分析地理空间影像。识别中心地理地点并估计地理范围（近似半径）。
Sequencer 将前述模块的响应组织并结构化为逻辑序列。
Solution Generator 使用 LLM 或 VLLM 基于结构化输入合成最终答案。
Answer Generator 对 Solution Generator 产生的解决方案进行精炼和验证。提取并检查预测答案的一致性。
表 10：Module Inventory 中对于解决地理空间查询必不可少的模块
工具 描述
Trip Tool 检索位置信息及它们之间的旅行路线。结合 Place Details 和 Directions API 获取地点元数据和逐步路线指引。
Route Tool 使用 Directions API 获取两点之间的路线信息，包括距离、预计时间和导航步骤。
Nearby Tool 使用 Nearby Search API 识别指定区域内的兴趣点。返回地点名称、评分及其他元数据。
PlaceInfo Tool 使用 Place Details API 检索给定地点的详细信息，包括地址、营业时间、联系信息和评论。
表 11：MapAgent 框架使用的地图工具，每个工具都构建在特定的 Google Maps API 之上。
LLM Backbone 数据集 Chameleon Octotools MapAgent (Ours)
GPT-3.5-Turbo
MapEval-API 7.0 12.0 6.0
MapEval-Textual 6.5 11.0 5.5
MapQA 6.0 10.0 5.0
Qwen-2.5-72B
MapEval-API 7.0 12.0 6.0
MapEval-Textual 6.5 11.0 5.5
MapQA 6.0 10.0 5.0
GPT-4o MapEval-Visual 8.0 14.0 7.0
Qwen-2.5-VL-72B MapEval-Visual 8.0 14.0 7.0
表 12：不同数据集和骨干模型下每次查询的平均 LLM API 调用次数比较。MapAgent 始终表现出更高的效率，所需 LLM API 交互次数少于基线。
1314

---

## 对应原文第 20 页

LLM Backbone Dataset Chameleon Octotools MapAgent (Ours)
GPT-3.5-Turbo
MapEval-API 4.5 8.0 3.0
MapEval-Textual 5.0 10.0 3.5
MapQA 4.0 7.0 2.5
Qwen-2.5-72B
MapEval-API 4.5 8.0 3.0
MapEval-Textual 5.0 10.0 3.5
MapQA 4.0 7.0 2.5
GPT-4o MapEval-Visual 6.0 10.0 4.0
Qwen-2.5-VL-72B MapEval-Visual 6.0 10.0 4.0
表 13：每次查询平均 token 消耗量（以千为单位，K）的比较。与基线相比，MapAgent 显著降低了 token 使用量，表明其上下文管理更加高效。
LLM Backbone Dataset Chameleon Octotools MapAgent (Ours)
GPT-3.5-Turbo
MapEval-API 2.0 6.0 2.0
MapEval-Textual 1.5 4.0 1.5
MapQA 1.0 3.0 1.0
Qwen-2.5-72B
MapEval-API 2.0 6.0 2.0
MapEval-Textual 1.5 4.0 1.5
MapQA 1.0 3.0 1.0
GPT-4o MapEval-Visual 2.0 5.0 2.0
Qwen-2.5-VL-72B MapEval-Visual 2.0 5.0 2.0
表 14：每次查询平均 Google Maps API 调用次数的比较。MapAgent 将工具使用降至最低，达到与基线持平或更优的水平。
LLM Backbone Dataset Chameleon Octotools MapAgent (Ours)
GPT-3.5-Turbo
MapEval-API 23.0 38.0 15.0
MapEval-Textual 20.0 34.0 13.0
MapQA 17.0 28.0 14.0
Qwen-2.5-72B
MapEval-API 29.0 42.0 20.0
MapEval-Textual 24.0 41.0 16.0
MapQA 22.0 36.0 15.0
GPT-4o MapEval-Visual 25.0 40.0 17.0
Qwen-2.5-VL-72B MapEval-Visual 32.0 46.0 22.0
表 15：每次查询平均执行时间（以秒为单位）的比较。与基线相比，MapAgent 在所有基准测试上均实现了显著更低的延迟。
1315

---

## 对应原文第 21 页

Listing 1：MapAgent 回答查询的示例 绿色：正确答案。红色：错误答案。
问题：
我目前在 Planetshakers Church Melbourne City Campus。我想开车去 Carrot Tattoo Studio，然后去 Melbourne Lifestyle Apartments - Docklands Accommodation。这会花多长时间？
选项：A. 18 mins B. 19 mins C. 20 mins D. 21 mins
Planner agent 选择的模块：
1. Map Service
2. Solution Generator
3. Answer Generator
Map Service 模块通过 Map-Tool Agent（调用 Trip tool）收集的信息：
所有位置信息：
Planetshakers Church Melbourne City Campus
名称：Planetshakers Church Melbourne City Campus
地址：400 City Rd, Southbank VIC 3006, Australia
评分：4.8
类型：church, tourist_attraction, place_of_worship, point_of_interest, establishment
当前是否营业：False
工作日营业时间：
- Monday：Closed
....
....
- Saturday：Closed
- Sunday：9:00 AM - 8:00 PM
Carrot Tattoo Studio
名称：Carrot Tattoo Studio
地址：Basement /63 Elizabeth St, Melbourne VIC 3000, Australia
评分：5
类型：store, point_of_interest, establishment
当前是否营业：False
工作日营业时间：
- Monday：10:00 AM - 8:00 PM
- Tuesday：10:00 AM - 8:00 PM
....
....
- Sunday：10:00 AM - 8:00 PM
Melbourne Lifestyle Apartments - Docklands Accommodation
名称：Melbourne Lifestyle Apartments - Best Views on Collins
地址：893 A Collins St, Docklands VIC 3008, Australia
评分：4.8
类型：lodging, point_of_interest, establishment
当前是否营业：True
工作日营业时间：
- Monday：Open 24 hours
- Tuesday：Open 24 hours
....
....
从 Planetshakers Church Melbourne City Campus 到 Carrot Tattoo Studio 的行程时间（距离）为 9 mins
（2.0 km）
从 Planetshakers Church Melbourne City Campus 到 Melbourne Lifestyle Apartments
- Docklands Accommodation 的行程时间（距离）为 8 mins（2.5 km）
从 Carrot Tattoo Studio 到 Planetshakers Church Melbourne City Campus 的行程时间（距离）为 9 mins
（1.9 km）
....
....
从 Melbourne Lifestyle Apartments - Docklands Accommodation 到 Carrot Tattoo
Studio 的行程时间（距离）为 11 mins（2.7 km）
solution_generator 模块生成的解答：
为了确定从 Planetshakers Church Melbourne City Campus 到 Carrot Tattoo Studio，
然后到 Melbourne Lifestyle Apartments - Docklands Accommodation 的总行程时间，我们需要将
每一段行程的行程时间相加。
1. **从 Planetshakers Church Melbourne City Campus 到 Carrot Tattoo Studio：**
- 行程时间：9 minutes
2. **从 Carrot Tattoo Studio 到 Melbourne Lifestyle Apartments - Docklands Accommodation：**
- 行程时间：10 minutes
现在，我们将这些行程时间相加：
9 minutes + 10 minutes = 19 minutes
因此，总行程时间是 19 minutes。
answer_generator 模块提取出的正确选项：B.19 minutes
1316

---

## 对应原文第 22 页

Listing 2: MapAgent 如何回答 MapEval-Visual 计数查询的示例 绿色：正确答案。红色：错误答案。
上下文：
问题：
地图下半部分可以看到多少座教堂？
选项：A. 五座 B. 两座 C. 四座 D. 三座
Planner agent 选择的模块：
从模块目录中选择的模块及其执行顺序：
1. Visual Place Recognizer 模块
2. map_service 模块
3. solution_generator 模块
4. answer_generator 模块
Visual Place Recognizer 模块输出：
该图像中心表示瑞典斯德哥尔摩 Radmansgatan 46, 113 57 的位置。
Map Service 模块输出：
执行 map_service 模块时，它会连接到内层（Inner Layer）中的 map-tool agent。
Map-Tool Agent 输出：
选择 Nearby 工具来获取信息。
Nearby 工具的输出：
在瑞典斯德哥尔摩 Radmansgatan 46, 113 57 位置 0.8 公里范围内有一些教堂，如下所示：
City Church（距离：0.46526450497253263 公里，评分：4.6，评论者总数：94）
St. Peter’s Church, Stockholm（距离：0.584886996790922 公里，评分：4.5，评论者总数：42）
Adolf Fredriks Forsamling（距离：0.36249979086127565 公里，评分：4.5，评论者总数：341）
solution generator 模块的输出：
根据提供的地图和 Google Maps 上下文，下半部分可见的教堂是：
St. Peter’s Church, Stockholm
Adolf Fredriks Forsamling
City Church
因此，正确答案是 B. 三座。
answer generator 模块的输出：
根据 solution generator 的响应，答案应为 3，这看起来合乎逻辑且正确。
答案是 B. 三座。
评论：
最终答案 B. 3 是正确答案
1317

---

## 对应原文第 23 页

Listing 3: MapAgent 回答 MapEval-Visual Route 查询的示例 绿色：正确答案。红色：错误答案。
上下文：
问题：
在 Cole Street Guesthouse 吃完午饭后，如何从 Seabird Water Taxi 前往 Sierra Leone Grammer School？
选项：
A . Seabird Water Taxi -> 沿 High Broad St 向西北方向朝 Andrews St 行进 -> 左转进入 Andrews St ->
继续进入 Andrew St -> 右转进入 Macaulay St -> Sierra Leone Grammar School -> 沿 Macaulay St 向东北方向行进 ->
在第 1 个十字路口左转朝 Cole St 方向 -> 在第 2 个十字路口左转进入
Cole St -> Cole Street Guesthouse
B . Seabird Water Taxi -> 沿 High Broad St 向西北方向朝 Andrews St 行进 -> 左转进入 Andrews St ->
继续进入 Andrew St -> 右转进入 Macaulay St -> Sierra Leone Grammar School
C . Seabird Water Taxi -> 沿 High Broad St 向西北方向朝 Andrews St 行进 -> 左转进入 Macaulay St ->
Sierra Leone Grammar School -> 沿 Macaulay St 向东北方向行进 -> 在第 1 个十字路口左转朝
Cole St 方向 -> 在第 2 个十字路口左转进入 Cole St -> Cole Street Guesthouse
D. Seabird Water Taxi -> 沿 High Broad St 向西北方向朝 Andrews St 行进 -> 右转朝 Cole St 方向 ->
在第 1 个十字路口左转进入 Cole St -> Cole Street Guesthouse -> 沿 Cole St 向东北方向朝
Damba Rd 行进 -> 在第 1 个十字路口右转朝 Macaulay St 方向 -> 在第 2 个十字路口右转
进入 Macaulay St -> Sierra Leone Grammar School
Planner agent 选择的模块：
从模块目录中选择的模块及其执行顺序：
1. Visual Place Recognizer 模块
2. map_service 模块
3. s o lu t i on _ g en e r at o r 模块
4. a nswer_ge nerator 模块
Image Search 模块输出：
该图像中心表示 Cole Street Guesthouse，5 Cole St，Freetown，Sierra Leone 的位置。
Map Service 模块输出：
执行 map_service 模块时，它连接到 Inner Layer 中的 map - tool agent。
Map-Tool Agent 输出：
选择 Route tool 来获取信息。
Route Tool 的输出：
从 Seabird Water Taxi，Freetown，Sierra Leone 到 Sierra Leone Grammar
School，Freetown，Sierra Leone 共有 1 条路线，途中经过 Cole Street Guesthouse。路线信息提供
如下：
Route 1:( VIA ) High Broad St (0.4 km，5 mins )
详细步骤如下：
沿 High Broad St 向西北方向朝 Andrews St 行进 (0.3 km，4 mins )
右转朝 Cole St 方向 (56 m，1 min )
左转进入 Cole St 目的地将在左侧 (46 m，1 min )
沿 cole st 向东北方向朝 Damba Rd 行进 (46 m，1 min )
在第 1 个十字路口右转朝 Macaulay St 方向 (110 m，1.5 min )
在第 2 个十字路口右转进入 Macaulay St (260 m，2 min )
Sierra Leone Grammar School
1318

---

## 对应原文第 24 页

Listing 4：MapAgent 如何回答 MapEval-Visual Route 查询的示例续篇 绿色：正确答案。
红色：错误答案。
solution generator 模块的输出：
基于提供的地图和 Google Maps 上下文，最佳路径点是：
沿 High Broad St 向西北方向前进，朝 Andrews St 方向
向右转，朝 Cole St 方向
向左转进入 Cole St目的地将在左侧
沿 cole st 向东北方向前进，朝 Damba Rd 方向
在第 1 个十字路口向右转，朝 Macaulay St 方向
在第 2 个十字路口向右转进入 Macaulay St
Sierra Leone Grammar School
因此正确答案是：
**( D ) Seabird Water Taxi
沿 High Broad St 向西北方向前进，朝 Andrews St 方向
向右转，朝 Cole St 方向
在第 1 个十字路口向左转进入 Cole St
Cole Street Guesthouse
沿 Cole St 向东北方向前进，朝 Damba Rd 方向
在第 1 个十字路口向右转，朝 Macaulay St 方向
在第 2 个十字路口向右转进入 Macaulay St
Sierra Leone Grammar School **
answer generator 模块的输出：
基于 solution generator 的响应，答案应为 D，这看起来合乎逻辑且正确。
答案是 D。Seabird Water Taxi -> 沿 High Broad St 向西北方向前进，朝 Andrews St 方向 -> 向右转
朝 Cole St 方向 -> 在第 1 个十字路口向左转进入 Cole St -> Cole Street Guesthouse -> 沿 Cole St 向东北方向
前进，朝 Damba Rd 方向 -> 在第 1 个十字路口向右转，朝 Macaulay St 方向 -> 在第 2
个十字路口向右转进入 Macaulay St -> Sierra Leone Grammar School
评论：
最终答案 D 是正确答案
1319

---

## 对应原文第 25 页

Listing 5：MapAgent 回答 MapEval-Visual Nearby 查询的示例 绿色：正确答案。红色：错误答案。
上下文：
问题：
哪座城堡距离 Howth 火车站最近？
选项：A.Howth Castle B . Mary Castle C . Claremont Castle D . Balscadden House
Planner agent 选择的模块：
从模块目录中选择的模块及其执行顺序：
1. v i s u a l _ p l a c e _ r e c o g n i z e r 模块
2. map_service 模块
3. s o lu t i on _ g en e r at o r 模块
4. a nswer_ge nerator 模块
Visual Place Recognizer 模块输出：
图像的中心似乎是爱尔兰的 Howth。
Map Service 模块输出：
执行 map_service 模块时，它连接到内层（Inner Layer）中的 map-tool agent。
Map-Tool Agent 输出：
选择 Nearby 工具以获取信息。
Nearby 工具的输出：
从当前位置 Howth Market , 3 Harbour Rd , Howth , Dublin , D13 T8Y7 , Ireland 出发，15 公里范围内有以下一些城堡距离：
Howth Castle Estate（距离：0. 4 7 70 5 7 68 7 9 84 5 4 42 公里，评分：4.1，评论总数：714）
Malahide Castle & Gardens（距离：8. 74 29 73 877 91 61 25 公里，评分：4.6，评论总数：15235）
Dublin Castle（距离：1 3 .8 7 5 69 7 8 94 0 2 49 6 1 公里，评分：4.3，评论总数：33876）
Swords Castle（距离：1 2 .5 4 8 38 7 0 08 4 0 38 0 4 公里，评分：4.5，评论总数：1764）
Dalkey Castle & Heritage Centre（距离：1 2 . 50 5 5 23 3 5 49 3 3 82 8 公里，评分：4.6，评论总数：911）
Monkstown Castle（距离：1 2. 2 3 54 5 2 66 7 3 77 2 0 6 公里，评分：4.4，评论总数：104）
Clontarf Castle Hotel（距离：9.267242 43435518 公里，评分：4.5，评论总数：5073）
Sandycove Castle（距离：11 .6217343 658077 公里，评分：4.5，评论总数：24）
Castle（距离：6. 94 31 23 269 96 79 69 公里，评分：4，评论总数：2）
Wooden Castle（距离：8. 66 25 82 766 43 53 69 公里，评分：4.6，评论总数：11）
Lambay Castle（距离：1 1 .9 0 1 97 3 3 02 2 9 07 7 2 公里，评分：4.3，评论总数：27）
Sutton Castle（距离：2 . 32 0 6 82 4 1 79 5 0 92 0 7 公里，评分：4.2，评论总数：9）
Archbold ’ s Castle（距离：1 2 .5 0 73 6 3 73 2 0 93 6 9 7 公里，评分：4.3，评论总数：8）
solution generator 模块的输出：
基于提供的地图和 Google Maps 上下文，距离 Howth 火车站最近的城堡是 Howth Castle，它距离 Howth 火车站仅 0.477 公里。
因此，正确答案是 A . Howth Castle
answer generator 模块的输出：
基于 solution generator 的响应，答案应该是 Howth Castle，这看起来合乎逻辑且正确。答案是 A. Howth Castle。
评论：
最终答案 A . Howth Castle 是正确答案
1320

---

## 对应原文第 26 页

Listing 6：示例 1，VLLM 如何使用 API 猜出正确答案。绿色：正确答案。红色：错误答案。
上下文：
问题：
地图下半部分可以看到多少座教堂？
选项：A. 五座 B. 两座 C. 四座 D. 三座
使用 API（MapAgent）的响应：
Google Map 响应：
在瑞典斯德哥尔摩 113 57，Radmansgatan 46 这一位置 0.8 公里范围内有一些教堂，如下所示：
City Church（距离：0.46526450497253263 公里，评分：4.6，总评论数：94）
St. Peter’s Church, Stockholm（距离：0.584886996790922 公里，评分：4.5，总评论数：42）
Adolf Fredriks Forsamling（距离：0.36249979086127565 公里，评分：4.5，总评论数：341）
来自解答生成器的最终答案：
“根据所提供的地图以及 google map 模块的上下文，地图下半部分可见的教堂是：”
“1. St. Peter’s Church, Stockholm”
“2. Adolf Fredriks Frsamling”
“3. City Church”
“因此，正确答案是：(D) 三座**”
不使用 API（Base Model）的响应：
根据所提供的地图，地图中有四座可见的教堂。因此，答案是：(C) 四座。
观察：
正确答案应该是 D. 三座，API 版本可以预测到，但没有 API 的 base model 无法回答。
1321

---

## 对应原文第 27 页

Listing 7：示例 2，VLLM 如何使用 API 猜出正确答案。绿色：正确答案。红色：错误答案。
上下文：
问题：
我在 Sagor Electronix 服务中心。离我最近的清真寺是哪一个？
选项：A. Kalumaria Mosque B. Al Ihsan Jame Mosque C. Komlapur Jame Masjid D. Mollikpur mosque
使用 API（MapAgent）的响应：
Google Map 响应：
从当前位置 Sagor Electronix 服务中心出发，有一些清真寺的距离如下：
Al Ihsan Jame Mosque（距离：0.5823095053737362 千米，评分：5，总评论数：1）
Mollikpur mosque（距离：1.1680710806133061 千米，评分：4.7，总评论数：3）
Kalumaria Mosque（距离：1.1879085293895582 千米，评分：4.3，总评论数：4）
Lolithar Bazar Central Masjid（距离：1.1566211819806247 千米，评分：0，总评论数：0）
Komlapur Jame Masjid（距离：1.8654544610349613 千米，评分：4.4，总评论数：25）
Rajshahi University Central Mosque（距离：4.459173025195116 千米，评分：4.9，总评论数：221）
Maria Jama Masjid（距离：1.8367913382567742 千米，评分：4，总评论数：9）
Maherchandi East Jame Mosque（距离：2.3601717780592995 千米，评分：5，总评论数：5）
Vodra Central Jame Mosque（距离：5.131809940553015 千米，评分：4.6，总评论数：145）
Madina Nagar Jame Mosque（距离：4.21188964565389 千米，评分：4.4，总评论数：57）
Purbo Para Jame Mosque（距离：3.614167437327442 千米，评分：4.2，总评论数：26）
Meherchandi Purbapara Central Jame Mosque（距离：3.4298745224188134 千米，评分：4.5，总评论数：69）
Katakhali Bazar Jame Masjid（距离：4.28092651862087 千米，评分：4.5，总评论数：193）
Belghoria Jama Masjid（距离：5.697832533309013 千米，评分：4.6，总评论数：19）
Hazrapukur Jame Mosque（距离：3.260713598861443 千米，评分：4.6，总评论数：30）
来自解决方案生成器的最终答案：
离你位置最近的清真寺是 **Al Ihsan Jame Mosque**，距离为 0.582 千米。\n\n答案：**(B) Al Ihsan Jame Mosque**
不使用 API（Base Model）的响应：
好的，我看到你在地图上的位置了！离 Sagor Electronix 服务中心最近的清真寺似乎是
(C) Kalumaria Mosque。
观察：
正确答案应该是 B。三个使用 API 的版本都能预测出来，但没有 API 的 base model 无法回答。
1322
