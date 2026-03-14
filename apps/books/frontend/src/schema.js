export default {
  id: 'books',
  name: 'Books',
  icon: '📚',
  description: 'Reading list and completed books',
  fields: [
    { id: 'title',         type: 'text',     label: 'Title',            required: true, displayInList: true },
    { id: 'author',        type: 'text',     label: 'Author',           displayInList: true },
    { id: 'category',      type: 'select',   label: 'Category',         options: ['Christian Living', 'Business/Entrepreneurship', 'Leadership', 'Communication', 'Fiction', 'Non-Fiction', 'Technical', 'Finance'], displayInList: true, filter: true },
    { id: 'status',        type: 'select',   label: 'Status',           options: ['to-read', 'reading', 'completed', 'abandoned'], default: 'to-read', displayInList: true, filter: true },
    { id: 'priority',      type: 'select',   label: 'Priority',         options: ['high', 'medium', 'low'], default: 'medium', filter: true },
    { id: 'startedDate',   type: 'date',     label: 'Started Reading',  showIf: { status: ['reading', 'completed', 'abandoned'] }, sortable: true },
    { id: 'completedDate', type: 'date',     label: 'Completed',        showIf: { status: ['completed'] }, sortable: true },
    { id: 'recommendedBy', type: 'text',     label: 'Recommended By' },
    { id: 'link',          type: 'text',     label: 'Link (Amazon, etc.)' },
    { id: 'notes',         type: 'textarea', label: 'Notes' }
  ],
  defaultSort: { field: 'title', order: 'asc' },
  views: { list: { groupBy: 'status' } }
};
