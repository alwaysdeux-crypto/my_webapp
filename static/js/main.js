document.addEventListener('DOMContentLoaded', () => {
    // State management
    let state = {
        status: 'all',
        category: 'all',
        priority: 'all',
        search: '',
        sortBy: 'due_date',
        todos: []
    };

    // DOM Elements
    const todoListContainer = document.getElementById('todo-list');
    const statTotalEl = document.getElementById('stat-total');
    const statPendingEl = document.getElementById('stat-pending');
    const statCompletedEl = document.getElementById('stat-completed');
    const statRateTextEl = document.getElementById('stat-rate-text');
    const statRateBarEl = document.getElementById('stat-rate-bar');
    const currentDateTextEl = document.getElementById('current-date-text');

    // Controls
    const statusTabs = document.getElementById('status-tabs');
    const searchInput = document.getElementById('search-input');
    const filterCategorySelect = document.getElementById('filter-category');
    const filterPrioritySelect = document.getElementById('filter-priority');
    const sortBySelect = document.getElementById('sort-by');

    // Modal & Form
    const modal = document.getElementById('todo-modal');
    const btnOpenCreateModal = document.getElementById('btn-open-create-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnCancelModal = document.getElementById('btn-cancel-modal');
    const todoForm = document.getElementById('todo-form');
    const formTodoId = document.getElementById('form-todo-id');
    const formTitle = document.getElementById('form-title');
    const formDescription = document.getElementById('form-description');
    const formCategory = document.getElementById('form-category');
    const formPriority = document.getElementById('form-priority');
    const formDueDate = document.getElementById('form-due-date');
    const modalTitle = document.getElementById('modal-title');

    // Display formatted today date
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    if (currentDateTextEl) {
        currentDateTextEl.textContent = today.toLocaleDateString('ko-KR', options);
    }

    // Initialize Data
    loadData();

    // Event Listeners for Filters
    if (statusTabs) {
        statusTabs.addEventListener('click', (e) => {
            const btn = e.target.closest('.tab-btn');
            if (!btn) return;
            
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            state.status = btn.dataset.status;
            loadTodos();
        });
    }

    if (searchInput) {
        let timer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                state.search = e.target.value.trim();
                loadTodos();
            }, 300);
        });
    }

    if (filterCategorySelect) {
        filterCategorySelect.addEventListener('change', (e) => {
            state.category = e.target.value;
            loadTodos();
        });
    }

    if (filterPrioritySelect) {
        filterPrioritySelect.addEventListener('change', (e) => {
            state.priority = e.target.value;
            loadTodos();
        });
    }

    if (sortBySelect) {
        sortBySelect.addEventListener('change', (e) => {
            state.sortBy = e.target.value;
            loadTodos();
        });
    }

    // Modal Open / Close
    btnOpenCreateModal.addEventListener('click', () => openModal());
    btnCloseModal.addEventListener('click', closeModal);
    btnCancelModal.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Form Submit (Create or Update)
    todoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const id = formTodoId.value;
        const payload = {
            title: formTitle.value.trim(),
            description: formDescription.value.trim(),
            category: formCategory.value,
            priority: formPriority.value,
            due_date: formDueDate.value
        };

        if (!payload.title) {
            showToast('할일 제목을 입력해주세요.', 'error');
            return;
        }

        try {
            let response;
            if (id) {
                // Update
                response = await fetch(`/api/todos/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create
                response = await fetch('/api/todos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || '저장에 실패했습니다.');
            }

            showToast(id ? '할일이 수정되었습니다 ✨' : '새 할일이 추가되었습니다 🎉', 'success');
            closeModal();
            loadData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    // Main Data Loading Function
    async function loadData() {
        await Promise.all([loadTodos(), loadStats()]);
    }

    // Fetch Todos API
    async function loadTodos() {
        try {
            const params = new URLSearchParams({
                status: state.status,
                category: state.category,
                priority: state.priority,
                search: state.search,
                sort_by: state.sortBy
            });

            const response = await fetch(`/api/todos?${params.toString()}`);
            if (!response.ok) throw new Error('데이터 전송 오류');
            
            const data = await response.json();
            state.todos = data;
            renderTodoList(data);
        } catch (err) {
            todoListContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <p>할일 목록을 불러오지 못했습니다.</p>
                </div>
            `;
        }
    }

    // Fetch Stats API
    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) return;
            
            const stats = await response.json();
            statTotalEl.textContent = stats.total;
            statPendingEl.textContent = stats.pending;
            statCompletedEl.textContent = stats.completed;
            statRateTextEl.textContent = `${stats.rate}%`;
            statRateBarEl.style.width = `${stats.rate}%`;
        } catch (err) {
            console.error('Stats error:', err);
        }
    }

    // Render Todo Cards
    function renderTodoList(todos) {
        if (!todos || todos.length === 0) {
            todoListContainer.innerHTML = `
                <div class="empty-state glass-card">
                    <i class="fa-solid fa-folder-open"></i>
                    <p>조건에 일치하는 할일이 없습니다.</p>
                </div>
            `;
            return;
        }

        todoListContainer.innerHTML = todos.map(todo => {
            const isCompleted = todo.completed === 1;
            const priorityBadge = getPriorityBadgeHtml(todo.priority);
            const dueDateFormatted = todo.due_date ? `📅 ${todo.due_date}` : '';
            
            return `
                <div class="todo-card glass-card ${isCompleted ? 'completed-card' : ''}" data-id="${todo.id}">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" class="todo-checkbox" ${isCompleted ? 'checked' : ''} data-id="${todo.id}">
                    </div>
                    
                    <div class="todo-content">
                        <div class="todo-title">${escapeHtml(todo.title)}</div>
                        ${todo.description ? `<div class="todo-desc">${escapeHtml(todo.description)}</div>` : ''}
                        
                        <div class="todo-meta">
                            ${priorityBadge}
                            <span class="badge badge-category"><i class="fa-solid fa-tag"></i> ${escapeHtml(todo.category)}</span>
                            ${dueDateFormatted ? `<span class="due-date-text">${dueDateFormatted}</span>` : ''}
                        </div>
                    </div>

                    <div class="todo-actions">
                        <button class="btn-icon btn-icon-edit" data-id="${todo.id}" title="수정">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                        <button class="btn-icon btn-icon-delete" data-id="${todo.id}" title="삭제">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        attachCardEvents();
    }

    // Event Delegation for Todo Cards
    function attachCardEvents() {
        // Toggle Completed
        document.querySelectorAll('.todo-checkbox').forEach(cb => {
            cb.addEventListener('change', async (e) => {
                const id = e.target.dataset.id;
                try {
                    const res = await fetch(`/api/todos/${id}/toggle`, { method: 'PATCH' });
                    if (!res.ok) throw new Error('상태 변경 실패');
                    loadData();
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });

        // Edit
        document.querySelectorAll('.btn-icon-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                const todo = state.todos.find(t => t.id == id);
                if (todo) openModal(todo);
            });
        });

        // Delete
        document.querySelectorAll('.btn-icon-delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.currentTarget.dataset.id;
                if (!confirm('정말 이 할일을 삭제하시겠습니까?')) return;

                try {
                    const res = await fetch(`/api/todos/${id}`, { method: 'DELETE' });
                    if (!res.ok) throw new Error('삭제 실패');
                    
                    showToast('할일이 삭제되었습니다.', 'info');
                    loadData();
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });
    }

    // Modal Helpers
    function openModal(todo = null) {
        todoForm.reset();
        if (todo) {
            modalTitle.innerHTML = '<i class="fa-solid fa-pen-to-square"></i> 할일 수정';
            formTodoId.value = todo.id;
            formTitle.value = todo.title || '';
            formDescription.value = todo.description || '';
            formCategory.value = todo.category || '업무';
            formPriority.value = todo.priority || '보통';
            formDueDate.value = todo.due_date || '';
        } else {
            modalTitle.innerHTML = '<i class="fa-solid fa-plus-circle"></i> 새 할일 등록';
            formTodoId.value = '';
            // Default due date to tomorrow
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            formDueDate.value = tomorrow.toISOString().split('T')[0];
        }
        modal.classList.add('active');
        formTitle.focus();
    }

    function closeModal() {
        modal.classList.remove('active');
    }

    // Utility Functions
    function getPriorityBadgeHtml(priority) {
        switch (priority) {
            case '긴급': return '<span class="badge badge-urgent">🚨 긴급</span>';
            case '높음': return '<span class="badge badge-high">🔥 높음</span>';
            case '보통': return '<span class="badge badge-medium">⚡ 보통</span>';
            case '낮음': return '<span class="badge badge-low">☕ 낮음</span>';
            default: return `<span class="badge badge-medium">${escapeHtml(priority)}</span>`;
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;')
                  .replace(/'/g, '&#039;');
    }

    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let iconHtml = '<i class="fa-solid fa-circle-info"></i>';
        if (type === 'success') iconHtml = '<i class="fa-solid fa-circle-check" style="color:#34d399"></i>';
        if (type === 'error') iconHtml = '<i class="fa-solid fa-circle-exclamation" style="color:#f87171"></i>';

        toast.innerHTML = `${iconHtml} <span>${escapeHtml(message)}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(50px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});
