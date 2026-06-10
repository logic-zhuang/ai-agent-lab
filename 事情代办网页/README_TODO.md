# 🎯 待办事项提醒工具

一个现代化的React网页待办事项管理工具，支持优先级、截止日期和本地数据持久化。

## 功能特性

- ✅ 添加、编辑、完成待办事项
- 📅 设置截止日期和优先级
- 🎨 现代化UI设计，响应式布局
- 💾 本地存储数据持久化
- 🔍 多条件过滤（全部/进行中/已完成）
- 📊 任务统计信息
- ⏰ 超期任务提醒
- 🚀 快速、轻量级

## 快速开始

### 环境要求
- Node.js 14+
- npm 或 yarn

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```
访问 `http://localhost:3000`

### 生产构建
```bash
npm run build
npm run preview
```

## 项目结构

```
├── src/
│   ├── App.jsx              # 主应用组件
│   ├── App.css              # 主样式
│   ├── index.css            # 全局样式
│   ├── main.jsx             # 入口文件
│   └── components/
│       ├── TodoForm.jsx     # 输入表单组件
│       ├── TodoForm.css
│       ├── TodoList.jsx     # 待办列表组件
│       ├── TodoList.css
│       ├── TodoItem.jsx     # 单个待办项组件
│       └── TodoItem.css
├── index.html               # HTML模板
├── package.json
├── vite.config.js
└── .gitignore
```

## 优化内容

- 📦 使用Vite作为构建工具（比Create React App快3倍）
- 🎭 组件化架构，易于维护和扩展
- 💅 CSS模块化，避免样式冲突
- 📱 移动端响应式设计
- 🔄 自动持久化到localStorage
- ⚡ 高性能的列表渲染和过滤

## 使用技巧

- **优先级排序**：高优先级任务自动显示在前面
- **超期提醒**：超过截止日期的任务会高亮显示
- **快速过滤**：点击按钮快速切换任务视图
- **数据同步**：所有数据自动保存到浏览器本地

祝你使用愉快！🚀
