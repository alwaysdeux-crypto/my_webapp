document.addEventListener('DOMContentLoaded', () => {
    let state = {
        search: '',
        profiles: []
    };

    const listContainer = document.getElementById('profile-list');
    const statTotalEl = document.getElementById('stat-total');
    const statMaleEl = document.getElementById('stat-male');
    const statFemaleEl = document.getElementById('stat-female');

    const searchInput = document.getElementById('search-input');

    const modal = document.getElementById('profile-modal');
    const btnOpenCreateModal = document.getElementById('btn-open-create-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnCancelModal = document.getElementById('btn-cancel-modal');
    const profileForm = document.getElementById('profile-form');
    const formProfileId = document.getElementById('form-profile-id');
    const formName = document.getElementById('form-name');
    const formGender = document.getElementById('form-gender');
    const formBirthDate = document.getElementById('form-birth-date');
    const formBirthTime = document.getElementById('form-birth-time');
    const formMemo = document.getElementById('form-memo');
    const modalTitle = document.getElementById('modal-title');

    loadData();

    if (searchInput) {
        let timer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                state.search = e.target.value.trim();
                loadProfiles();
            }, 300);
        });
    }

    btnOpenCreateModal.addEventListener('click', () => openModal());
    btnCloseModal.addEventListener('click', closeModal);
    btnCancelModal.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const id = formProfileId.value;
        const payload = {
            name: formName.value.trim(),
            gender: formGender.value,
            birth_date: formBirthDate.value,
            birth_time: formBirthTime.value,
            memo: formMemo.value.trim()
        };

        if (!payload.name) {
            showToast('이름을 입력해주세요.', 'error');
            return;
        }
        if (!payload.birth_date) {
            showToast('생년월일을 입력해주세요.', 'error');
            return;
        }

        try {
            let response;
            if (id) {
                response = await fetch(`/api/profiles/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                response = await fetch('/api/profiles', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || '저장에 실패했습니다.');
            }

            showToast(id ? '사주 정보가 수정되었습니다 ✨' : '새 사주가 등록되었습니다 🎉', 'success');
            closeModal();
            loadData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    async function loadData() {
        await Promise.all([loadProfiles(), loadStats()]);
    }

    async function loadProfiles() {
        try {
            const params = new URLSearchParams({ search: state.search });
            const response = await fetch(`/api/profiles?${params.toString()}`);
            if (!response.ok) throw new Error('데이터 전송 오류');

            const data = await response.json();
            state.profiles = data;
            renderProfileList(data);
        } catch (err) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <p>프로필 목록을 불러오지 못했습니다.</p>
                </div>
            `;
        }
    }

    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) return;

            const stats = await response.json();
            statTotalEl.textContent = stats.total;
            statMaleEl.textContent = stats.male;
            statFemaleEl.textContent = stats.female;
        } catch (err) {
            console.error('Stats error:', err);
        }
    }

    const ELEMENT_ORDER = ['목', '화', '토', '금', '수'];
    const ELEMENT_LABEL = { 목: '목(木)', 화: '화(火)', 토: '토(土)', 금: '금(金)', 수: '수(水)' };

    function renderProfileList(profiles) {
        if (!profiles || profiles.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state glass-card">
                    <i class="fa-solid fa-folder-open"></i>
                    <p>등록된 사주 프로필이 없습니다.</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = profiles.map(profile => {
            const genderClass = profile.gender === '여' ? 'female' : 'male';
            const genderIcon = profile.gender === '여' ? 'fa-venus' : 'fa-mars';
            const birthText = profile.birth_time
                ? `${profile.birth_date} ${profile.birth_time}`
                : `${profile.birth_date} (시간 미상)`;

            return `
                <div class="profile-card glass-card" data-id="${profile.id}">
                    <div class="profile-card-header">
                        <div class="profile-identity">
                            <div class="gender-icon ${genderClass}"><i class="fa-solid ${genderIcon}"></i></div>
                            <div>
                                <div class="profile-name">${escapeHtml(profile.name)}</div>
                                <div class="profile-birth-text"><i class="fa-solid fa-cake-candles"></i> ${birthText}</div>
                            </div>
                        </div>
                        <div class="profile-actions">
                            <button class="btn-icon btn-icon-edit" data-id="${profile.id}" title="수정">
                                <i class="fa-solid fa-pen"></i>
                            </button>
                            <button class="btn-icon btn-icon-delete" data-id="${profile.id}" title="삭제">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </div>
                    </div>

                    ${renderPillarsTable(profile.pillars)}
                    ${renderElementsBar(profile.elements)}
                    ${profile.memo ? `<div class="profile-memo">${escapeHtml(profile.memo)}</div>` : ''}
                </div>
            `;
        }).join('');

        attachCardEvents();
    }

    function renderPillarsTable(pillars) {
        const cols = [
            { label: '년주', p: pillars.year },
            { label: '월주', p: pillars.month },
            { label: '일주', p: pillars.day },
            { label: '시주', p: pillars.hour },
        ];

        return `
            <div class="pillars-table">
                ${cols.map(c => {
                    if (!c.p) {
                        return `
                            <div class="pillar-col empty">
                                <div class="pillar-label">${c.label}</div>
                                <div class="pillar-hanja">-</div>
                                <div class="pillar-hangul">시간 미상</div>
                            </div>
                        `;
                    }
                    return `
                        <div class="pillar-col">
                            <div class="pillar-label">${c.label}</div>
                            <div class="pillar-hanja">
                                <span class="ch-stem el-${c.p.stem_element}">${c.p.stem_hanja}</span>
                                <span class="ch-branch el-${c.p.branch_element}">${c.p.branch_hanja}</span>
                            </div>
                            <div class="pillar-hangul">${c.p.ganzhi}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    function renderElementsBar(elements) {
        const total = ELEMENT_ORDER.reduce((sum, el) => sum + (elements[el] || 0), 0) || 1;
        const segs = ELEMENT_ORDER.map(el => {
            const count = elements[el] || 0;
            const pct = (count / total) * 100;
            return `<div class="elements-bar-seg bg-el-${el}" style="width:${pct}%"></div>`;
        }).join('');

        const legend = ELEMENT_ORDER.map(el => `
            <span><span class="legend-dot bg-el-${el}"></span>${ELEMENT_LABEL[el]} ${elements[el] || 0}</span>
        `).join('');

        return `
            <div class="elements-bar">${segs}</div>
            <div class="elements-legend">${legend}</div>
        `;
    }

    function attachCardEvents() {
        document.querySelectorAll('.btn-icon-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                const profile = state.profiles.find(p => p.id == id);
                if (profile) openModal(profile);
            });
        });

        document.querySelectorAll('.btn-icon-delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.currentTarget.dataset.id;
                if (!confirm('정말 이 프로필을 삭제하시겠습니까?')) return;

                try {
                    const res = await fetch(`/api/profiles/${id}`, { method: 'DELETE' });
                    if (!res.ok) throw new Error('삭제 실패');

                    showToast('프로필이 삭제되었습니다.', 'info');
                    loadData();
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });
    }

    function openModal(profile = null) {
        profileForm.reset();
        if (profile) {
            modalTitle.innerHTML = '<i class="fa-solid fa-pen-to-square"></i> 사주 정보 수정';
            formProfileId.value = profile.id;
            formName.value = profile.name || '';
            formGender.value = profile.gender || '남';
            formBirthDate.value = profile.birth_date || '';
            formBirthTime.value = profile.birth_time || '';
            formMemo.value = profile.memo || '';
        } else {
            modalTitle.innerHTML = '<i class="fa-solid fa-plus-circle"></i> 새 사주 등록';
            formProfileId.value = '';
        }
        modal.classList.add('active');
        formName.focus();
    }

    function closeModal() {
        modal.classList.remove('active');
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
        if (type === 'success') iconHtml = '<i class="fa-solid fa-circle-check" style="color:#4ade80"></i>';
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
