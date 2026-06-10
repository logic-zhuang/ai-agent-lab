import { useState } from 'react'
import './TodoForm.css'

export default function TodoForm({ onAdd }) {
  const [text, setText] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [priority, setPriority] = useState('medium')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (text.trim()) {
      onAdd(text, dueDate, priority)
      setText('')
      setDueDate('')
      setPriority('medium')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="todo-form">
      <div className="form-content">
        <input
          type="text"
          placeholder="输入新的待办事项..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="input-text"
        />
        <input
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          className="input-date"
        />
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          className="input-priority"
        >
          <option value="low">低</option>
          <option value="medium">中</option>
          <option value="high">高</option>
        </select>
        <button type="submit" className="btn-add">
          添加
        </button>
      </div>
    </form>
  )
}
