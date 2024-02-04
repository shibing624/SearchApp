[**🇨🇳中文**](https://github.com/shibing624/SmartSearch/blob/main/README_zh.md) | [**🌐English**](https://github.com/shibing624/SmartSearch/blob/main/README.md) 

<div align="center">
    <a href="https://github.com/shibing624/SmartSearch">
    <img src="https://github.com/shibing624/SmartSearch/blob/main/docs/icon.svg" height="50" alt="Logo">
    </a>
    <br/>
    <a href="https://search.mulanai.com/" target="_blank"> Online Demo </a>
    <br/>
    <img width="70%" src="https://github.com/shibing624/SmartSearch/blob/main/docs/screenshot.png">
</div>

-----------------

# SmartSearch: Build your own conversational search engine with LLMs
[![HF Models](https://img.shields.io/badge/Hugging%20Face-shibing624-green)](https://huggingface.co/shibing624)
[![Github Stars](https://img.shields.io/github/stars/shibing624/SmartSearch?color=yellow)](https://star-history.com/#shibing624/SmartSearch&Timeline)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![python_version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](requirements.txt)
[![GitHub issues](https://img.shields.io/github/issues/shibing624/SmartSearch.svg)](https://github.com/shibing624/SmartSearch/issues)
[![Wechat Group](https://img.shields.io/badge/wechat-group-green.svg?logo=wechat)](#Contact)


## Features
- 内置支持开源LLM，可用本地模型搭建API
- 支持OpenAI LLM API，可用`gpt-4`
- 内置支持bing/google搜索引擎
- 可定制的美观UI界面
- 可分享，缓存搜索结果
- 支持问题追问，连续问答
- 支持query分析，基于上下文重写query，精准搜索

## 安装依赖

```shell
pip install -r requirements.txt
```


## 运行

### 1. 构建前端web

两种方法构建前端：
1. 下载打包好的前端ui，https://github.com/shibing624/SmartSearch/releases/download/0.1.0/ui.zip 解压到项目根目录直接使用。
2. 自己使用npm构建前端（需要nodejs 18以上版本）
```shell
cd web && npm install && npm run build
```
输出：项目根目录产出`ui`文件夹，包含前端静态文件。

### 2. 基于Lepton API运行服务

> [!NOTE]
> 我们推荐使用内置llm和kv函数。
> 运行以下命令以自动设置它们。

```shell
lep login
python search.py
```
好了，现在你的搜索应用正在运行：http://0.0.0.0:8081

- 提供在线colab运行服务demo：[demo.ipynb](https://github.com/shibing624/SmartSearch/blob/main/demo.ipynb)，其对应的colab：[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shibing624/SmartSearch/blob/main/demo.ipynb)
## 使用搜索引擎API
你可以使用Bing或者Google Search的API运行服务。
### 使用Bing搜索的API

要使用Bing Web Search API，请访问[此链接](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)获取您的Bing订阅密钥。

```shell
export BING_SEARCH_V7_SUBSCRIPTION_KEY=YOUR_BING_SUBSCRIPTION_KEY
BACKEND=BING python search.py
```
### 使用Google搜索的API 
你有三种方法使用Google Search API：
1. 选择使用来自SearchApi的[SearchApi Google Search API](https://www.searchapi.io/)
2. 选择使用Serper的 [Serper Google Search API](https://www.serper.dev)
3. 选择由Google提供的[Programmable Search Engine](https://developers.google.com/custom-search)

对于使用SearchApi的Google搜索：

```shell
export SEARCHAPI_API_KEY=YOUR_SEARCHAPI_API_KEY
BACKEND=SEARCHAPI python search.py
```

对于使用Serper的Google搜索：

```shell
export SERPER_SEARCH_API_KEY=YOUR_SERPER_API_KEY
BACKEND=SERPER python search.py
```

对于使用Programmable Search Engine的Google搜索：

```shell
export GOOGLE_SEARCH_API_KEY=YOUR_GOOGLE_SEARCH_API_KEY
export GOOGLE_SEARCH_CX=YOUR_GOOGLE_SEARCH_ENGINE_ID
BACKEND=GOOGLE python search.py
```

## 使用OpenAI LLM
如果你追求更好LLM生成效果，你可以使用OpenAI的LLM模型`gpt-4`。

```shell
export SERPER_SEARCH_API_KEY=YOUR_SERPER_API_KEY
export OPENAI_API_KEY=YOUR_OPENAI_API_KEY
export OPENAI_BASE_URL=https://xxx/v1
BACKEND=SERPER LLM_TYPE=OPENAI LLM_MODEL=gpt-4 python search.py
```

## 配置

以下是部署配置，见`search.py`：

* `resource_shape`：大多数重型工作将由LLM服务器和搜索引擎API完成，因此您可以选择一个小资源形状。`cpu.small`通常就足够好。

然后，设置以下环境变量。

* `BACKEND`：要使用的搜索后端。如果你没有设置bing或google，只需使用`LEPTON`尝试演示。否则，请做 `BING`, `GOOGLE`, `SERPER` 或者 `SEARCHAPI`
* `LLM_TYPE`：要使用的LLM类型。如果您正在使用Lepton，请将其设置为`lepton`。否则，将其设置为`openai`。
* `LLM_MODEL`: 运行的LLM模型。我们建议使用`mixtral-8x7b`, 但如果你想尝试其他模型, 你可以尝试在LeptonAI上托管的那些, 比如说, `llama2-70b`, `llama2-13b`, `llama2-7b`. 注意小模型可能效果不佳
* `KV_NAME`: 存储搜索结果所用到的Lepton KV. 可以使用默认值`smart-search`
* `RELATED_QUESTIONS`: 是否生成相关问题. 如果设定为'true', 搜索引擎会为你生成相关问题. 否则就不会
* `REWRITE_QUESTION`：是否重写问题。如果您将此设置为`true`，LLM将重写问题并将其发送到搜索引擎。否则，它不会
* `GOOGLE_SEARCH_CX`: 如果正在使用谷歌官方API，请指定搜索cx。否则请留空
* `LEPTON_ENABLE_AUTH_BY_COOKIE`: 允许Web UI访问部署。将其设为'true'
* `OPENAI_BASE_URL`: 如果您正在使用OpenAI，可以指定基础url。通常为`https://api.openai.com/v1`
* `ENABLE_HISTORY`：是否启用历史记录。如果您将此设置为`true`，LLM将存储搜索历史记录。否则，它不会

此外，您还可以设置以下KEY：

* `LEPTON_WORKSPACE_TOKEN`: 这是调用Lepton的LLM和KV apis所必需的。你可以在[Settings](https://dashboard.lepton.ai/workspace-redirect/settings)找到你的workspace token
* `BING_SEARCH_V7_SUBSCRIPTION_KEY`: 如果正在使用Bing, 需要指定订阅密钥. 否则不需要
* `GOOGLE_SEARCH_API_KEY`: 如果正在使用Google, 需要指定搜索api密钥. 注意也应该在环境中指定cx. 如果没有使用Google，则不需要
* `SEARCHAPI_API_KEY`: 如果正在使用SearchApi，一个第三方谷歌搜索API，需要指定api密钥
* `OPENAI_API_KEY`: 如果正在使用OpenAI, 需要指定api密钥


## Todo
- 支持多轮检索，主要是页面显示多轮检索结果
- 支持第三方LLM的API，如qwen、baichuan等
- 小程序端支持，目前只支持web端
- 使用Agent判定是否需要改写query，以及主动反问用户补充问题，提升搜索准确率

## Contact
- Issue(建议)：[![GitHub issues](https://img.shields.io/github/issues/shibing624/SmartSearch.svg)](https://github.com/shibing624/SmartSearch/issues)
- 邮件我：xuming: xuming624@qq.com
- 微信我：加我*微信号：xuming624, 备注：姓名-公司-NLP* 进NLP交流群。


## License
授权协议为 [The Apache License 2.0](LICENSE)，可免费用做商业用途。请在产品说明中附加SmartSearch的链接和授权协议。


## Contribute
项目代码还很粗糙，如果大家对代码有所改进，欢迎提交回本项目。

## Reference
- [leptonai/search_with_lepton](https://github.com/leptonai/search_with_lepton/tree/main)
