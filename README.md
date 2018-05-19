# housekeeper

A housekeeper bot for *Capital of Statistics* posts.

## 简介

这是一个机器人。

对于 <https://github.com/cosname/cosx.org> 的文章，自动进行某些检查和评论。

作为一个 Python 编写 Github 机器人的范例，这个可以稍作修改用于别的 repo 之上。

## 安装与部署

1. 创建一个 Github 机器人账号。
2. 把本 repo 代码部署在一台 vps 上，然后参照 `.env-example` 设定 `.env` 文件。接着安装 Python 相应软件包，之后就可以 `flask run` 运行代码了。本代码开发于 `python3`，但是尽可能地兼容 `python2`。
3. 去到想要被监听的 repo 里面，设置 webhook 地址。
4. 那么，每当被监听 repo 有新的事件的时候，本机器人就会做出对应动作。

## 功能

现在实现了以下功能：

1. 对于 `First-time contributor`，打个招呼。
2. 对于投稿到 `content/post/` 下的 pull request，进行必要的格式检查：文件名要规范、图片介绍不能为空、yaml meta 要按照格式。
3. 对于 issue 里面 at 到机器人账号的，打个招呼。
