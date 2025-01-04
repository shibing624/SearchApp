[**🇨🇳中文**](https://github.com/shibing624/SearchGPT/blob/main/README_zh.md) | [**🌐English**](https://github.com/shibing624/SearchGPT/blob/main/README.md) 

<div align="center">
    <a href="https://github.com/shibing624/SearchGPT">
    <img src="https://github.com/shibing624/SearchGPT/blob/main/docs/icon.svg" height="50" alt="Logo">
    </a>
    <br/>
    <a href="https://search.mulanai.com/" target="_blank"> Online Demo </a>
    <br/>
    <img width="70%" src="https://github.com/shibing624/SearchGPT/blob/main/docs/screenshot.png">
</div>

-----------------

# SearchGPT: Build your own conversational search engine with LLMs
[![HF Models](https://img.shields.io/badge/Hugging%20Face-shibing624-green)](https://huggingface.co/shibing624)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![python_version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](requirements.txt)
[![GitHub issues](https://img.shields.io/github/issues/shibing624/SearchGPT.svg)](https://github.com/shibing624/SearchGPT/issues)
[![Wechat Group](https://img.shields.io/badge/wechat-group-green.svg?logo=wechat)](#Contact)


## Features
- 支持多种大模型厂商的模型，包括OpenAI/ZhipuAI API，推荐用免费的`glm-4-flash`
- 内置支持google serper/DDGS/ZhipuAI SearchPro搜索引擎(免费，推荐)
- 可定制的美观UI界面
- 可分享，缓存搜索结果
- 支持猜你想问，连续问答

## 安装依赖

```shell
pip install -r requirements.txt
```


## 运行

```shell
python search.py
```
好了，现在你的搜索应用正在运行：http://0.0.0.0:8081

- 查看FastAPI服务：http://0.0.0.0:8081/docs
- 提供在线colab运行服务demo：[demo.ipynb](https://github.com/shibing624/SearchGPT/blob/main/demo.ipynb)，其对应的colab：[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shibing624/SearchGPT/blob/main/demo.ipynb)

### rebuild前端web

两种方法构建前端：
1. 下载打包好的前端ui，https://github.com/shibing624/SearchGPT/releases/download/0.1.0/ui.zip 解压到项目根目录直接使用。
2. 自己使用npm构建前端（需要nodejs 18以上版本）
```shell
cd web && npm install && npm run build
```
输出：项目根目录产出`ui`文件夹，包含前端静态文件。

## 使用搜索引擎API
使用Serper的Google搜索：

```shell
export SERPER_SEARCH_API_KEY=YOUR_SERPER_API_KEY
BACKEND=SERPER python search.py
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

部署配置，见[search.py](https://github.com/shibing624/SearchGPT/blob/main/search.py)：

设置以下环境变量：

* `BACKEND`：要使用的搜索后端。默认使用ZhipuAI的免费搜索工具`SEARCHPRO`。否则，请设置为`SERPER`，并搭配填写相应的API_KEY，或者使用开源搜索引擎`DDGS`。
* `LLM_TYPE`：要使用的LLM类型。默认设置为`ZHIPUAI`。否则，将其设置为`OPENAI`，需要设置对应的LLM API key。
* `LLM_MODEL`: 运行的LLM模型。我们建议使用免费的`glm-4-flash`, 或者使用其他的模型，但需要跟上面的`LLM_TYPE`配套。
* `RELATED_QUESTIONS`: 是否生成相关问题. 如果设定为`true`, 搜索引擎会为你生成相关问题. 否则就不会
* `ENABLE_HISTORY`：是否启用历史记录。如果您将此设置为`true`，LLM将存储搜索历史记录。否则，它不会

此外，您还可以设置以下KEY：

* `ZHIPUAI_API_KEY`: 如果正在使用ZhipuAI, 需要指定api密钥
* `OPENAI_API_KEY`: 如果正在使用OpenAI, 需要指定api密钥
* `SERPER_SEARCH_API_KEY`: 如果正在使用serper的Google, 需要指定搜索api密钥

## Contact
- Issue(建议)：[![GitHub issues](https://img.shields.io/github/issues/shibing624/SearchGPT.svg)](https://github.com/shibing624/SearchGPT/issues)
- 邮件我：xuming: xuming624@qq.com
- 微信我：加我*微信号：xuming624, 备注：姓名-公司-NLP* 进NLP交流群。

<img src="docs/wechat.jpeg" width="200" />

## License
授权协议为 [The Apache License 2.0](LICENSE)，可免费用做商业用途。请在产品说明中附加SearchGPT的链接和授权协议。


## Contribute
项目代码还很粗糙，如果大家对代码有所改进，欢迎提交回本项目。

## Reference
- [leptonai/search_with_lepton](https://github.com/leptonai/search_with_lepton/tree/main)
