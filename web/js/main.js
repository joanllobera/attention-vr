let allData = [];
let filteredData = [];
let currentPage = 1;
let recordsPerPage = 10;
let sortColumn = null;
let sortDirection = 'asc';

// CSV 파일 로드 - Jekyll 환경에 맞게 수정
async function loadCSV() {
    try {
        // CSV 파일 경로 설정
        const response = await fetch('data/vla_data.csv');
        const text = await response.text();
        
        // Papa Parse로 CSV 파싱
        const result = Papa.parse(text, {
            header: true,
            skipEmptyLines: true,
            dynamicTyping: true
        });
        
        if (result.errors.length > 0) {
            console.error('CSV parsing errors:', result.errors);
        }
        
        allData = result.data;
        
        // 카테고리 우선순위에 따라 정렬
        const categoryOrder = ['Review', 'End-to-End', '3D', 'Planning', 'Policy', 'Special'];
        allData.sort((a, b) => {
            const aCat = (a['カテゴリ'] || '').split(',')[0].trim();
            const bCat = (b['カテゴリ'] || '').split(',')[0].trim();
            
            const aIndex = categoryOrder.indexOf(aCat);
            const bIndex = categoryOrder.indexOf(bCat);
            
            // 우선순위에 있는 카테고리가 먼저 오도록
            if (aIndex !== -1 && bIndex !== -1) {
                return aIndex - bIndex;
            } else if (aIndex !== -1) {
                return -1;
            } else if (bIndex !== -1) {
                return 1;
            }
            
            // 우선순위에 없는 카테고리는 알파벳 순
            return aCat.localeCompare(bCat);
        });
        
        filteredData = [...allData];
        
        populateFilters();
        updateTable();
        updatePagination();
    } catch (error) {
        console.error('Error loading CSV:', error);
        document.getElementById('tableBody').innerHTML = 
            '<tr><td colspan="15" class="loading">Error loading CSV file. Please ensure vla_data.csv is in the data directory.</td></tr>';
    }
}

// 필터 옵션 채우기
function populateFilters() {
    // 카테고리를 쉼표로 분리하여 개별 태그로 처리
    const categories = [...new Set(allData.flatMap(row => 
        (row['カテゴリ'] || '').split(',').map(c => c.trim()).filter(c => c)
    ))];
    const tasks = [...new Set(allData.flatMap(row => (row['タスク'] || '').split(', ')).filter(v => v))];
    const modalities = [...new Set(allData.flatMap(row => (row['Modality'] || '').split(', ')).filter(v => v))];
    const robots = [...new Set(allData.flatMap(row => (row['ロボット'] || '').split(', ')).filter(v => v))];
    const backbones = [...new Set(allData.flatMap(row => (row['Backbone'] || '').split(', ')).filter(v => v))];
    
    populateSelect('categoryFilter', categories);
    populateSelect('taskFilter', tasks);
    populateSelect('modalityFilter', modalities);
    populateSelect('robotFilter', robots);
    populateSelect('backboneFilter', backbones);
}

function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">All</option>';
    options.sort().forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        select.appendChild(optionElement);
    });
}

// 태그 클래스 생성 함수
function getTagClass(type, value) {
    const normalizedValue = value.toLowerCase().replace(/[\s-]/g, '-');
    return `tag tag-${type}-${normalizedValue}`;
}

// 검색어 하이라이트 함수
function highlightSearchTerm(text, searchTerm) {
    if (!text || !searchTerm || searchTerm.length < 2) return text;
    
    // HTML 엔티티 이스케이프
    const escapeHtml = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };
    
    // 정규식 특수문자 이스케이프
    const escapeRegExp = (str) => {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    };
    
    const safeText = escapeHtml(text);
    const regex = new RegExp(`(${escapeRegExp(searchTerm)})`, 'gi');
    return safeText.replace(regex, '<mark>$1</mark>');
}

// 테이블 업데이트
function updateTable() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    
    const searchTerm = document.getElementById('searchInput').value.trim();
    const start = (currentPage - 1) * recordsPerPage;
    const end = start + recordsPerPage;
    const pageData = filteredData.slice(start, end);
    
    if (pageData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="15" style="text-align: center;">No data found</td></tr>';
        return;
    }
    
    pageData.forEach(row => {
        const tr = document.createElement('tr');
        
        // Category - 태그로 표시
        const categories = (row['カテゴリ'] || '').split(',').filter(c => c.trim());
        tr.innerHTML += `<td>${categories.map(c => {
            const trimmed = c.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="${getTagClass('category', trimmed)}">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Abbreviation
        const abbreviation = searchTerm ? highlightSearchTerm(row['略称'] || '', searchTerm) : (row['略称'] || '');
        tr.innerHTML += `<td><strong>${abbreviation}</strong></td>`;
        
        // Title
        const title = searchTerm ? highlightSearchTerm(row['タイトル'] || '', searchTerm) : (row['タイトル'] || '');
        tr.innerHTML += `<td class="wrap">${title}</td>`;
        
        // Conference
        const conference = searchTerm ? highlightSearchTerm(row['学会'] || '', searchTerm) : (row['学会'] || '');
        tr.innerHTML += `<td>${conference}</td>`;
        
        // Paper URL
        const paperUrl = row['Paper URL'] || '';
        tr.innerHTML += `<td>${paperUrl ? `<a href="${paperUrl}" target="_blank" class="link">Paper</a>` : ''}</td>`;
        
        // Website URL
        const websiteUrl = row['Website URL'] || '';
        tr.innerHTML += `<td>${websiteUrl ? `<a href="${websiteUrl}" target="_blank" class="link">Website</a>` : ''}</td>`;
        
        // Task
        const tasks = (row['タスク'] || '').split(',').filter(t => t.trim());
        tr.innerHTML += `<td>${tasks.map(t => {
            const trimmed = t.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="${getTagClass('task', trimmed)}">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Domain
        const domains = (row['Domain'] || '').split(',').filter(d => d.trim());
        tr.innerHTML += `<td>${domains.map(d => {
            const trimmed = d.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="${getTagClass('domain', trimmed)}">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Robot
        const robots = (row['ロボット'] || '').split(',').filter(r => r.trim());
        tr.innerHTML += `<td>${robots.map(r => {
            const trimmed = r.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="tag tag-default">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Training
        const training = (row['Training'] || '').split(',').filter(t => t.trim());
        tr.innerHTML += `<td>${training.map(t => {
            const trimmed = t.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="tag tag-default">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Evaluation
        const evaluations = (row['Evaluation'] || '').split(',').filter(e => e.trim());
        tr.innerHTML += `<td>${evaluations.map(e => {
            const trimmed = e.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="${getTagClass('evaluation', trimmed)}">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Modality
        const modalities = (row['Modality'] || '').split(',').filter(m => m.trim());
        tr.innerHTML += `<td>${modalities.map(m => {
            const trimmed = m.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="${getTagClass('modality', trimmed)}">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Dataset
        const datasets = (row['Dataset'] || '').split(',').filter(d => d.trim());
        tr.innerHTML += `<td>${datasets.map(d => {
            const trimmed = d.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="tag tag-default">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Backbone
        const backbones = (row['Backbone'] || '').split(',').filter(b => b.trim());
        tr.innerHTML += `<td>${backbones.map(b => {
            const trimmed = b.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="tag tag-default">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        // Action Generation
        const actionGen = (row['Action Generation'] || '').split(',').filter(a => a.trim());
        tr.innerHTML += `<td>${actionGen.map(a => {
            const trimmed = a.trim();
            const highlighted = searchTerm ? highlightSearchTerm(trimmed, searchTerm) : trimmed;
            return `<span class="tag tag-default">${highlighted}</span>`;
        }).join(' ')}</td>`;
        
        tbody.appendChild(tr);
    });
}

// 검색 점수 계산
function calculateSearchScore(searchTerm, row) {
    const fieldWeights = {
        '略称': 10,
        'タイトル': 8,
        'カテゴリ': 6,
        'タスク': 5,
        'Modality': 3
    };
    
    let score = 0;
    const searchLower = searchTerm.toLowerCase();
    
    for (const [field, value] of Object.entries(row)) {
        if (!value) continue;
        
        const valueLower = String(value).toLowerCase();
        const weight = fieldWeights[field] || 1;
        
        if (valueLower === searchLower) {
            score += weight * 10;
        } else if (valueLower.split(/\s+/).some(word => word.startsWith(searchLower))) {
            score += weight * 5;
        } else if (valueLower.includes(searchLower)) {
            score += weight * 2;
        }
    }
    
    return score;
}

// 필터링
function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const taskFilter = document.getElementById('taskFilter').value;
    const modalityFilter = document.getElementById('modalityFilter').value;
    const robotFilter = document.getElementById('robotFilter').value;
    const backboneFilter = document.getElementById('backboneFilter').value;
    
    // 필터링 및 점수 계산
    const results = allData.map(row => {
        // 기본 필터
        if (categoryFilter && !(row['カテゴリ'] || '').split(',').some(c => c.trim() === categoryFilter)) return null;
        if (taskFilter && !(row['タスク'] || '').includes(taskFilter)) return null;
        if (modalityFilter && !(row['Modality'] || '').includes(modalityFilter)) return null;
        if (robotFilter && !(row['ロボット'] || '').includes(robotFilter)) return null;
        if (backboneFilter && !(row['Backbone'] || '').includes(backboneFilter)) return null;
        
        // 검색어 매칭 및 점수 계산
        if (searchTerm) {
            const score = calculateSearchScore(searchTerm, row);
            if (score === 0) {
                // 점수가 0이면 일반 검색
                const searchMatch = Object.values(row).some(value => 
                    String(value).toLowerCase().includes(searchTerm)
                );
                if (!searchMatch) return null;
            }
            return { row, score };
        }
        
        return { row, score: 0 };
    }).filter(item => item !== null);
    
    // 점수 기반 정렬
    if (searchTerm && results.some(item => item.score > 0)) {
        results.sort((a, b) => b.score - a.score);
    }
    
    filteredData = results.map(item => item.row);
    
    currentPage = 1;
    updateTable();
    updatePagination();
}

// 정렬
function sortTable(column) {
    if (sortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortDirection = 'asc';
    }
    
    const columnMap = {
        0: 'カテゴリ',
        1: '略称',
        2: 'タイトル',
        3: '学会',
        7: 'タスク',
        8: 'Domain',
        9: 'ロボット',
        10: 'Training',
        11: 'Evaluation',
        12: 'Modality',
        13: 'Dataset',
        14: 'Backbone',
        15: 'Action Generation'
    };
    
    const key = columnMap[column];
    
    filteredData.sort((a, b) => {
        let aVal = a[key] || '';
        let bVal = b[key] || '';
        
        // 카테고리의 경우 첫 번째 태그로 정렬
        if (key === 'カテゴリ') {
            aVal = aVal.split(',')[0].trim() || '';
            bVal = bVal.split(',')[0].trim() || '';
        }
        
        if (sortDirection === 'asc') {
            return aVal.localeCompare(bVal);
        } else {
            return bVal.localeCompare(aVal);
        }
    });
    
    // Update sort indicators
    document.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    const currentTh = document.querySelector(`th[data-column="${column}"]`);
    if (currentTh) {
        currentTh.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
    }
    
    updateTable();
}

// 페이지네이션 업데이트
function updatePagination() {
    const totalRecords = filteredData.length;
    const totalPages = Math.ceil(totalRecords / recordsPerPage);
    const start = totalRecords > 0 ? (currentPage - 1) * recordsPerPage + 1 : 0;
    const end = Math.min(currentPage * recordsPerPage, totalRecords);
    
    document.getElementById('startRecord').textContent = start;
    document.getElementById('endRecord').textContent = end;
    document.getElementById('totalRecords').textContent = totalRecords;
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages || 1;
    
    document.getElementById('firstPage').disabled = currentPage === 1;
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage >= totalPages;
    document.getElementById('lastPage').disabled = currentPage >= totalPages;
}

// 페이지 변경
function changePage(newPage) {
    const totalPages = Math.ceil(filteredData.length / recordsPerPage);
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        updateTable();
        updatePagination();
    }
}

// 필터 초기화
function clearAllFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('taskFilter').value = '';
    document.getElementById('modalityFilter').value = '';
    document.getElementById('robotFilter').value = '';
    document.getElementById('backboneFilter').value = '';
    applyFilters();
}

// 이벤트 리스너 설정
document.addEventListener('DOMContentLoaded', function() {
    loadCSV();
    
    // 필터 이벤트
    document.getElementById('searchInput').addEventListener('input', applyFilters);
    document.getElementById('categoryFilter').addEventListener('change', applyFilters);
    document.getElementById('taskFilter').addEventListener('change', applyFilters);
    document.getElementById('modalityFilter').addEventListener('change', applyFilters);
    document.getElementById('robotFilter').addEventListener('change', applyFilters);
    document.getElementById('backboneFilter').addEventListener('change', applyFilters);
    
    // 정렬 이벤트
    document.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', () => sortTable(parseInt(th.dataset.column)));
    });
    
    // 페이지네이션 이벤트
    document.getElementById('firstPage').addEventListener('click', () => changePage(1));
    document.getElementById('prevPage').addEventListener('click', () => changePage(currentPage - 1));
    document.getElementById('nextPage').addEventListener('click', () => changePage(currentPage + 1));
    document.getElementById('lastPage').addEventListener('click', () => {
        const totalPages = Math.ceil(filteredData.length / recordsPerPage);
        changePage(totalPages);
    });
    
    document.getElementById('recordsPerPage').addEventListener('change', (e) => {
        recordsPerPage = parseInt(e.target.value);
        currentPage = 1;
        updateTable();
        updatePagination();
    });
});
