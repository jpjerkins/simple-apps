export default {
  id: 'todos',
  name: 'To-Do List',
  icon: '✓',
  description: 'Simple task tracker',
  fields: [
    { id: 'title',   type: 'text',     label: 'Task',     required: true, displayInList: true },
    { id: 'status',  type: 'select',   label: 'Status',   options: ['pending', 'in-progress', 'done'], default: 'pending', displayInList: true, filter: true },
    { id: 'dueDate', type: 'date',     label: 'Due Date', sortable: true },
    { id: 'notes',   type: 'textarea', label: 'Notes' }
  ],
  defaultSort: { field: 'dueDate', order: 'asc' }
};
