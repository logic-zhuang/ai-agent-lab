import './TodoItem.css'

const priorityEmoji = {
  low: '🟢',
  medium: '🟡',
  high: '🔴'
}

const priorityLabel = {
  low: '低',
  medium: '中',
  high: '高'
}

export default function TodoItem({ todo, onToggle, onDelete }) {
  const formatDate = (date) => {
    if (!date) return ''
    return new Date(date).toLocaleDateString('zh-CN')
  }

  const isOverdue = () => {
    if (!todo.dueDate || todo.completed) return false
    return new Date(todo.dueDate) < new Date()
  }

  return (
    <div className={`todo-item ${todo.completed ? 'completed' : ''} ${isOverdue() ? 'overdue' : ''}`}>
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => onToggle(todo.id)}
        className="checkbox"
      />
      <div className="todo-content">
        <div className="todo-text">{todo.text}</div>
        <div className="todo-meta">
          <span className="priority-badge">
            {priorityEmoji[todo.priority]} {priorityLabel[todo.priority]}
          </span>
          {todo.dueDate && (
            <span className={`date-badge ${isOverdue() ? 'overdue-date' : ''}`}>
              📅 {formatDate(todo.dueDate)}
            </span>
          )}
        </div>
      </div>
      <button
        onClick={() => onDelete(todo.id)}
        className="btn-delete"
        title="删除"
      >
        ✕
      </button>
    </div>
  )
}
