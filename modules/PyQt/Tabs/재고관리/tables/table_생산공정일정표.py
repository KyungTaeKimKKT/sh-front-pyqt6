공정_구분 = {
    'HI': ['하도',],
    'PO': ['분체', 'UHC'],
}


# HI_설비_구분 = {
#     'base': ['Main1', 'Main2', 'Main3'],
#     'MT': ['MT-1', 'MT-2', 'INK']
# }


from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime, timedelta

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime, timedelta


from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime, timedelta

class ProcessScheduleModel(QAbstractTableModel):
    def __init__(self, 생산계획list, 휴일list, dday_obj, 공정_구분, productionLine):
        super().__init__()
        # 기본 정보 컬럼 정의
        self.info_columns = ['id', '생산지시_fk','고객사', '구분', 'Job_Name', 'Proj_No', '출하_type','비고','소재', '치수', '계획수량']
        self.info_column_count = len(self.info_columns)

        # 기존 계획 데이터 처리 수정
        self.plans = [plan for plan in 생산계획list 
                     if plan.get('HI일정') is not None and plan.get('계획수량', 0) > 0]
        self.plans = sorted(self.plans, key=lambda x: x['id'])

        # 공정상세 데이터 초기화
        self._initialize_process_details()

        self.holidays = set(h['휴일'] for h in 휴일list)
        self.process_types = 공정_구분
        self.dday = dday_obj
        self.productionLine = productionLine
        
        self.equipment_assignments = {}  # 설비 할당 정보 저장
        # 날짜 범위 계산 (HI일정 기준)
        if self.plans:  # plans가 비어있지 않은 경우에만 계산
            self.start_date = min(datetime.strptime(plan['HI일정'], '%Y-%m-%d').date() 
                                for plan in self.plans)
            self.end_date = max(datetime.strptime(plan['HI일정'], '%Y-%m-%d').date() 
                               for plan in self.plans)
        else:  # plans가 비어있는 경우 기본값 설정
            self.start_date = datetime.now().date()
            self.end_date = datetime.now().date()

        self.date_range = self._generate_date_range()
        
        # 공정 일정 계산
        self.schedule_data = self._calculate_schedule()

        # 일별 수량 합계 계산 추가
        self.daily_sums = self._calculate_daily_sums()

                # 변경 사항 추적을 위한 딕셔너리 추가
        self.changes = {}  # {plan_id: {'original': {}, 'current': {}}}

    def _initialize_process_details(self):
        """공정상세 데이터 초기화"""
        self.process_details = {}
        for plan in self.plans:
            plan_id = plan['id']
            self.process_details[plan_id] = {}
            
            # 공정상세_set이 있는 경우 처리
            if '공정상세_set' in plan:
                for detail in plan['공정상세_set']:
                    if detail['is_active']:
                        process_name = detail['공정명']
                        self.process_details[plan_id][process_name] = {
                            'date': datetime.strptime(detail['계획일'], '%Y-%m-%d').date(),
                            'equipment_id': detail['ProductionLine_fk'],
                            'order': detail['공정순서']
                        }

    def setEquipment(self, plan_id, process, equipment):
        """설비 할당 정보 설정"""
        if plan_id not in self.changes:
            self.changes[plan_id] = {
                'original': {
                    'equipment': self.equipment_assignments.get(plan_id, {}).copy(),
                    'dates': {k: v for k, v in self.schedule_data[plan_id]['processes'].items()}
                },
                'current': {
                    'equipment': self.equipment_assignments.get(plan_id, {}).copy(),
                    'dates': {k: v for k, v in self.schedule_data[plan_id]['processes'].items()}
                }
            }
        
        if plan_id not in self.equipment_assignments:
            self.equipment_assignments[plan_id] = {}
        self.equipment_assignments[plan_id][process] = equipment
        self.changes[plan_id]['current']['equipment'] = self.equipment_assignments[plan_id].copy()
        self.layoutChanged.emit()

    def setProcessDate(self, plan_id, process, new_date):
        """특정 공정의 날짜를 변경"""
        try:
            if plan_id in self.schedule_data:
                # 변경 사항 추적을 위한 초기 상태 저장
                if plan_id not in self.changes:
                    original_dates = {}
                    # 공정상세_set에서 원본 데이터 찾기
                    plan = next((p for p in self.plans if p['id'] == plan_id), None)
                    if plan and '공정상세_set' in plan:
                        for detail in plan['공정상세_set']:
                            if detail['is_active'] and detail['공정명'] == process:
                                original_dates[process] = datetime.strptime(detail['계획일'], '%Y-%m-%d').date()

                    self.changes[plan_id] = {
                        'original': {
                            'equipment': self.equipment_assignments.get(plan_id, {}).copy(),
                            'dates': original_dates or {k: v for k, v in self.schedule_data[plan_id]['processes'].items()}
                        },
                        'current': {
                            'equipment': self.equipment_assignments.get(plan_id, {}).copy(),
                            'dates': {k: v for k, v in self.schedule_data[plan_id]['processes'].items()}
                        }
                    }
                
                # 날짜 형식 통일
                if isinstance(new_date, str):
                    new_date = datetime.strptime(new_date, '%Y-%m-%d').date()
                elif isinstance(new_date, datetime):
                    new_date = new_date.date()
                
                # 해당 날짜에 이미 있는 공정들 찾기
                existing_processes = []
                for proc, date in self.schedule_data[plan_id]['processes'].items():
                    if date == new_date and proc != process:
                        existing_processes.append(proc)
                
                # 새로운 공정 추가
                self.schedule_data[plan_id]['processes'][process] = new_date
                self.changes[plan_id]['current']['dates'][process] = new_date
                
                # 기존 공정들 유지
                for existing_proc in existing_processes:
                    self.schedule_data[plan_id]['processes'][existing_proc] = new_date
                    self.changes[plan_id]['current']['dates'][existing_proc] = new_date

                self.daily_sums = self._calculate_daily_sums()
                self.layoutChanged.emit()
                return True
            return False
        except Exception as e:

            return False

    def moveRow(self, source_row, target_row):
        if source_row == target_row:
            return
            
        # 데이터 이동
        plan = self.plans.pop(source_row)
        self.plans.insert(target_row, plan)
        
        # 뷰 업데이트
        self.layoutChanged.emit()


    def _get_process_type(self, process):
        # 공정 타입 결정 (HI 또는 PO)
        for type_key, type_procs in self.process_types.items():
            if any(p in process for p in type_procs):
                return type_key
        return 'HI'  # 기본값

    def _calculate_start_date(self):
        # 가장 이른 시작일 계산 (출하일 기준 가장 긴 공정 기간)
        min_days = min(v for k, v in self.dday.items() if k.startswith('_'))
        return datetime.now().date() + timedelta(days=min_days)

    def _calculate_end_date(self):
        # 가장 늦은 종료일 (현재 날짜 기준)
        return datetime.now().date()

    def _generate_date_range(self):
        dates = []
        current = self.start_date
        while current <= self.end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def _calculate_schedule(self):
        schedule = {}
        for plan in self.plans:
            plan_id = plan['id']
            schedule[plan_id] = {
                'info': {
                    '고객사': plan.get('고객사'),
                    '구분': plan.get('구분'),
                    'Job_Name': plan.get('Job_Name'),
                    'Proj_No': plan.get('Proj_No'),
                    '소재': plan.get('소재'),
                    '치수': plan.get('치수'),
                    '계획수량': plan.get('계획수량')
                },
                'processes': {},
                'HI일정': plan.get('HI일정')
            }
            
            # 공정상세_set이 있고 비어있지 않은 경우
            if plan.get('공정상세_set') and len(plan['공정상세_set']) > 0:
                for proc_name, proc_info in self.process_details[plan_id].items():
                    schedule[plan_id]['processes'][proc_name] = proc_info['date']
                    
                    # 설비 할당 정보도 업데이트
                    if proc_info['equipment_id']:
                        if plan_id not in self.equipment_assignments:
                            self.equipment_assignments[plan_id] = {}
                        # equipment_id를 설비 이름으로 변환
                        equipment_name = next(
                            (line['name'] for line in self.productionLine 
                             if line['id'] == proc_info['equipment_id']),
                            None
                        )
                        if equipment_name:
                            self.equipment_assignments[plan_id][proc_name] = equipment_name
            else:
                # 기존 로직 (공정상세 데이터가 없는 경우)
                if plan['HI일정']:
                    상세공정_raw = plan['상세Process'].replace('\n', ' ').strip()
                    상세공정 = [p.strip() for p in 상세공정_raw.split('+') if p.strip()]
                    
                    hi_processes = [p for p in 상세공정 
                                if self._get_process_type(p) == 'HI']
                    if hi_processes:
                        end_date = datetime.strptime(plan['HI일정'], '%Y-%m-%d').date()
                        for i, proc in enumerate(reversed(hi_processes)):
                            proc_date = end_date - timedelta(days=i)
                            schedule[plan_id]['processes'][proc] = proc_date

        return schedule
        

    def _get_plan_processes(self, plan):
        processes = {}
        상세공정 = plan['상세Process'].split('+')
        
        for proc in 상세공정:
            proc = proc.strip()
            # 공정 타입 결정 (HI 또는 PO)
            proc_type = 'HI'  # 기본값
            for type_key, type_procs in self.process_types.items():
                if any(p in proc for p in type_procs):
                    proc_type = type_key
                    break
            
            # 공정 날짜 계산
            due_date = self.end_date + timedelta(days=self.dday[f'_{proc_type}'])
            processes[proc] = due_date
            
        return processes

    def rowCount(self, parent=None):
         return len(self.plans) + 1  # 합계 행 추가

    def columnCount(self, parent=None):
        return len(self.date_range) + self.info_column_count  # 하드코딩된 8 대신 동적 계산된 컬럼 수 사용

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
            
        row = index.row()
        col = index.column()

        # 첫 번째 행 - 일별 합계
        if row == 0:
            if role == Qt.ItemDataRole.BackgroundRole:
                return QColor('yellow')
            elif role == Qt.ItemDataRole.ForegroundRole:
                return QColor('black')
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setBold(True)
                return font
            elif role == Qt.ItemDataRole.DisplayRole:
                if col < self.info_column_count:
                    return '합계' if col == 0 else ''  # 첫 번째 컬럼만 '합계' 표시
                date = self.date_range[col - self.info_column_count]
                return str(self.daily_sums.get(date, 0))
            return None

        # 나머지 행 - 기존 로직
        actual_row = row - 1  # 실제 데이터 행 인덱스 조정
        plan = self.plans[actual_row]
        plan_id = self.plans[actual_row]['id']

        
        if role == Qt.ItemDataRole.DecorationRole and col >= self.info_column_count :
            # 설비 할당된 공정에 대한 아이콘 표시
            process = self.data(index, Qt.ItemDataRole.DisplayRole)
            if process and plan_id in self.equipment_assignments:
                if process in self.equipment_assignments[plan_id]:
                    equipment = self.equipment_assignments[plan_id][process]
                    icon_path = f"icons/{equipment.lower()}.png"

                    try:
                        if QFile.exists(icon_path):
                            return QIcon(icon_path)
                        else:
                            # 아이콘 파일이 없는 경우 텍스트 아이콘 생성
                            return self._create_text_icon(equipment)
                    except Exception as e:

                        return self._create_text_icon(equipment)

            
        if role == Qt.ItemDataRole.DisplayRole:
            if col < self.info_column_count:  # 기본 정보 컬럼 (동적으로 처리)
                column_name = self.info_columns[col]
                return str(plan.get(column_name, ''))
                
            # 날짜 컬럼 처리
            date_col = self.date_range[col - self.info_column_count]
            processes_for_date = []
            
            # 해당 날짜의 공정들을 상세공정 순서대로 정렬하여 표시
            if plan_id in self.schedule_data:
                # 원래 상세공정 순서 가져오기
                상세공정_raw = plan['상세Process']
                상세공정 = [p.strip() for p in 상세공정_raw.replace('\n', ' ').split('+') if p.strip()]
                
                # 현재 날짜의 공정들 수집
                processes_for_date = []
                for proc, proc_date in self.schedule_data[plan_id]['processes'].items():
                    if isinstance(proc_date, datetime):
                        proc_date = proc_date.date()
                    if proc_date == date_col:
                        # 설비 정보 가져오기
                        equipment = self.equipment_assignments.get(plan_id, {}).get(proc)
                        if equipment:
                            processes_for_date.append(f"[{equipment}] {proc}")
                        else:
                            processes_for_date.append(proc)
                
                # 원래 순서대로 정렬
                processes_for_date.sort(key=lambda x: 상세공정.index(x.split('] ')[-1] if ']' in x else x))
                
                return '\n'.join(processes_for_date) if processes_for_date else ''
                
            return ''



    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
            
        if orientation == Qt.Orientation.Horizontal:
            if section < self.info_column_count:  # 기본 정보 헤더 (동적으로 처리)
                return self.info_columns[section]
            
            date = self.date_range[section - self.info_column_count]
            date_str = date.strftime('%Y-%m-%d')
            
            # 휴일 표시
            if date_str in self.holidays:
                return f"{date_str}\n(휴일)"
            return date_str
            
        return str(section + 1)

    def _get_process_for_date(self, date, processes):
        # 날짜를 문자열로 변환하여 비교
        date_str = date.strftime('%Y-%m-%d')
        day_processes = []
        for proc, proc_date in processes.items():
            if isinstance(proc_date, datetime):
                proc_date = proc_date.date()
            if proc_date.strftime('%Y-%m-%d') == date_str:
                day_processes.append(proc)
        
        return '\n'.join(day_processes) if day_processes else ''
    

    def _calculate_daily_sums(self):
        """각 날짜별 설비 기준 수량 합계 계산"""
        # 모든 날짜에 대해 0으로 초기화
        sums = {date: 0 for date in self.date_range}
        processed_combinations = {}  # {(plan_id, date): set(equipment/no_equipment)}

        for plan_id, schedule in self.schedule_data.items():
            plan_info = next(p for p in self.plans if p['id'] == plan_id)
            plan_quantity = plan_info.get('계획수량', 0)

            # 모든 공정과 날짜 처리
            for proc, proc_date in schedule['processes'].items():
                # datetime 객체를 date 객체로 변환
                if isinstance(proc_date, datetime):
                    proc_date = proc_date.date()
                elif isinstance(proc_date, str):
                    proc_date = datetime.strptime(proc_date, '%Y-%m-%d').date()

                # 날짜가 현재 범위 내에 있는지 확인하고, 해당 날짜의 합계 계산
                if proc_date in sums:
                    key = (plan_id, proc_date)
                    if key not in processed_combinations:
                        processed_combinations[key] = set()

                    equipment = self.equipment_assignments.get(plan_id, {}).get(proc)
                    equipment_key = equipment if equipment else 'no_equipment'

                    # 해당 계획-날짜 조합에 대해 새로운 설비인 경우에만 수량 추가
                    if equipment_key not in processed_combinations[key]:
                        sums[proc_date] += plan_quantity
                        processed_combinations[key].add(equipment_key)

        return sums

    def save_current(self):
        """현재 모든 데이터를 DRF 모델 형식으로 반환
        - 신규 데이터(id: -1)와 변경된 기존 데이터만 반환
        """

        result_data = []
        
        for plan_id, schedule in self.schedule_data.items():
            plan = next(p for p in self.plans if p['id'] == plan_id)
            
            # 공정상세_set에서 기존 데이터 매핑
            existing_details = {}
            if '공정상세_set' in plan:
                for detail in plan['공정상세_set']:
                    if detail['is_active']:
                        existing_details[detail['공정명']] = detail

            # 현재 공정 데이터 처리
            for proc_name, proc_date in schedule['processes'].items():
                # 설비 정보 가져오기
                equipment_id = None
                if plan_id in self.equipment_assignments and proc_name in self.equipment_assignments[plan_id]:
                    equipment_name = self.equipment_assignments[plan_id][proc_name]
                    equipment_id = next(
                        (line['id'] for line in self.productionLine 
                        if line['name'] == equipment_name),
                        None
                    )

                # 기존 데이터 확인
                existing_detail = existing_details.get(proc_name)
                detail_id = existing_detail['id'] if existing_detail else -1
                
                # 변경 여부 확인
                is_changed = True
                if existing_detail:
                    existing_date = datetime.strptime(existing_detail['계획일'], '%Y-%m-%d').date()
                    is_changed = (
                        existing_date != proc_date or
                        existing_detail['ProductionLine_fk'] != equipment_id
                    )

                if is_changed or detail_id == -1:  # 변경되었거나 신규인 경우
                    current_data = {
                        'id': detail_id,
                        'is_active': True,
                        '확정Branch_fk': plan_id,
                        '공정순서': existing_detail['공정순서'] if existing_detail else 1,
                        '공정명': proc_name,
                        'ProductionLine_fk': equipment_id,
                        '계획일': proc_date.strftime('%Y-%m-%d')
                    }
                    result_data.append(current_data)

        # 확정Branch_fk와 공정순서로 정렬
        result_data.sort(key=lambda x: (x['확정Branch_fk'], x['공정순서']))
        return result_data

    def save_current_by_공정상세Set(self):
        """현재 모든 데이터를 공정상세_set(equipment) 단위로 DRF 모델 형식으로 반환
        - 신규 데이터(id: -1)와 변경된 기존 데이터만 반환
        """
        result_data = []
        
        # 임시 저장소: (확정Branch_fk, equipment_id, 날짜) 를 키로 사용
        grouped_processes = {}
        
        for plan_id, schedule in self.schedule_data.items():
            plan = next(p for p in self.plans if p['id'] == plan_id)
            
            # 공정상세_set에서 기존 데이터 매핑
            existing_details = {}
            if '공정상세_set' in plan:
                for detail in plan['공정상세_set']:
                    if detail['is_active']:
                        key = (detail['확정Branch_fk'], detail['ProductionLine_fk'], detail['계획일'])
                        if key not in existing_details:
                            existing_details[key] = []
                        existing_details[key].append(detail)

            # 현재 공정 데이터 처리
            for proc_name, proc_date in schedule['processes'].items():
                # 설비 정보 가져오기
                equipment_id = None
                equipment_name = None
                if plan_id in self.equipment_assignments and proc_name in self.equipment_assignments[plan_id]:
                    equipment_name = self.equipment_assignments[plan_id][proc_name]
                    equipment_id = next(
                        (line['id'] for line in self.productionLine 
                        if line['name'] == equipment_name),
                        None
                    )

                # 날짜 형식 통일
                if isinstance(proc_date, datetime):
                    proc_date = proc_date.date()
                proc_date_str = proc_date.strftime('%Y-%m-%d')

                # 그룹화 키 생성
                group_key = (plan_id, equipment_id, proc_date_str)
                
                if group_key not in grouped_processes:
                    grouped_processes[group_key] = {
                        'processes': [],
                        'equipment_id': equipment_id,
                        'equipment_name': equipment_name,
                        'date': proc_date_str,
                        'plan_id': plan_id
                    }
                grouped_processes[group_key]['processes'].append(proc_name)

        # 그룹화된 데이터를 결과 형식으로 변환
        for group_key, group_data in grouped_processes.items():
            plan_id, equipment_id, date = group_key
            
            # 공정명을 정렬하고 결합
            sorted_processes = sorted(group_data['processes'])
            combined_process = ' + '.join(sorted_processes)

            # 기존 detail ID 찾기
            existing_key = (plan_id, equipment_id, date)
            existing_detail = existing_details.get(existing_key, [{}])[0] if existing_details else {}
            detail_id = existing_detail.get('id', -1)

            current_data = {
                'id': detail_id,
                'is_active': True,
                '확정Branch_fk': plan_id,
                '공정순서': existing_detail.get('공정순서', 1),
                '공정명': combined_process,
                'ProductionLine_fk': equipment_id,
                'equipment_name': group_data['equipment_name'],
                '계획일': date
            }
            result_data.append(current_data)

        # 확정Branch_fk와 공정순서로 정렬
        result_data.sort(key=lambda x: (x['확정Branch_fk'], x['공정순서']))
        return result_data

    def get_changes(self):
        """변경된 데이터만 추출"""
        changed_data = []
        
        for plan_id, change_info in self.changes.items():
            original = change_info['original']
            current = change_info['current']
            
            # 설비 변경 확인
            equipment_changes = {}
            for process, equipment in current['equipment'].items():
                if process not in original['equipment'] or original['equipment'][process] != equipment:
                    equipment_changes[process] = equipment
            
            # 날짜 변경 확인
            date_changes = {}
            for process, date in current['dates'].items():
                if process not in original['dates'] or original['dates'][process] != date:
                    date_changes[process] = date.strftime('%Y-%m-%d')
            
            # 변경사항이 있는 경우만 추가
            if equipment_changes or date_changes:
                for process in set(equipment_changes.keys()) | set(date_changes.keys()):
                    changed_data.append({
                        'id': plan_id,
                        '공정': process,
                        'equipment': equipment_changes.get(process, None),
                        '생산일자': date_changes.get(process, None)
                    })
        
        return changed_data


    # ProcessScheduleModel 클래스에 메서드 추가
    def _create_text_icon(self, text):
        """텍스트 기반 아이콘 생성"""
        # 더 큰 크기의 아이콘 생성
        size = 32  # 크기를 32x32로 증가
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        # 안티앨리어싱 적용
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # 폰트 설정
        font = QFont()
        font.setPointSize(8)  # 폰트 크기 조정
        painter.setFont(font)
        
        # 텍스트 그리기
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
        return QIcon(pixmap)

class DraggableTableView(QTableView):
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableView.DragDropMode.InternalMove)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.drag_start_position = None
        self.drag_item_data = None

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid() or index.row() == 0:
            return

        processes = self.model().data(index, Qt.ItemDataRole.DisplayRole)
        if not processes or '\n' not in processes:  # 병합된 공정이 아닌 경우
            return

        menu = QMenu(self)
        split_action = menu.addAction("공정 분리")
        action = menu.exec(self.mapToGlobal(pos))
        
        if action == split_action:
            self.split_processes(index)

    def split_processes(self, index):
        processes = self.model().data(index, Qt.ItemDataRole.DisplayRole)
        if not processes:
            return

        process_list = processes.split('\n')
        if len(process_list) <= 1:
            return

        # 분리할 공정 선택 다이얼로그
        dialog = ProcessSplitDialog(process_list, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # 선택된 공정들과 날짜 가져오기
        selected_processes = dialog.get_selected_processes()
        target_date = dialog.get_target_date()
        
        if not selected_processes or not target_date:
            return

        # 현재 계획 ID 가져오기
        actual_row = index.row() - 1
        plan_id = self.model().plans[actual_row]['id']

        # 선택된 공정들을 새로운 날짜로 이동
        for process in selected_processes:
            # '[설비명]' 형식이 있다면 제거
            if ']' in process:
                process = process.split(']')[1].strip()
            self.model().setProcessDate(plan_id, process, target_date)

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        # 합계 행(row=0)인 경우 무시
        if not index.isValid() or index.row() == 0:
            return

        if index.isValid() and index.column() >= self.model().info_column_count:
            processes = self.model().data(index, Qt.ItemDataRole.DisplayRole)
            if processes:
                dialog = EquipmentAssignmentDialog(processes, self)
                
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    plan_id = self.model().plans[index.row()-1]['id']
                    equipment = dialog.get_selected_equipment()
                    selected_processes = dialog.get_selected_processes()
                    
                    # 선택된 모든 공정에 대해 설비 할당
                    for process in selected_processes:
                        if dialog.apply_to_all():
                            date = self.model().date_range[index.column() - self.model().info_column_count]
                            for row in range(1, self.model().rowCount()):
                                curr_index = self.model().index(row, index.column())
                                curr_process = self.model().data(curr_index, Qt.ItemDataRole.DisplayRole)
                                if process in curr_process:
                                    curr_plan_id = self.model().plans[row-1]['id']
                                    self.model().setEquipment(curr_plan_id, process, equipment)
                        else:
                            self.model().setEquipment(plan_id, process, equipment)


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            index = self.indexAt(self.drag_start_position)
            if index.isValid() and index.column() >= self.model().info_column_count:  # 하드코딩된 4 대신 동적 계산  # 날짜 컬럼만
                if index.row() == 0:  # 합계 행은 드래그 불가
                    return
                actual_row = index.row() - 1  # 실제 데이터 행 인덱스 조정
                data = self.model().data(index, Qt.ItemDataRole.DisplayRole)
                if data:  # 공정 데이터가 있는 경우만
                    source_date = self.model().date_range[index.column() - self.model().info_column_count]
                    # 날짜를 문자열로 변환
                    # source_date_str = source_date.strftime('%Y-%m-%d')
                    self.drag_item_data = {
                        'plan_id': self.model().plans[actual_row]['id'],  # actual_row 사용
                        'process': data,
                        'source_date':source_date.strftime('%Y-%m-%d')
                    }

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self.drag_start_position:
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10:  # 드래그 시작 거리 임계값 감소
            return
        if not self.drag_item_data:
            return

        # 드래그 시작 시 시각적 피드백 추가
        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setText(str(self.drag_item_data))
        drag.setMimeData(mimedata)

        # 드래그 시 보여질 텍스트 이미지 생성
        pixmap = QPixmap(100, 30)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.drawText(0, 20, self.drag_item_data['process'])
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(5, 15))

        result = drag.exec(Qt.DropAction.MoveAction)
        if result == Qt.DropAction.MoveAction:
            self.drag_start_position = None
            self.drag_item_data = None

    def dropEvent(self, event):
        if not event.mimeData().hasText():

            event.ignore()
            return

        drop_pos = event.position().toPoint()
        drop_index = self.indexAt(drop_pos)
        
        if not drop_index.isValid() or drop_index.column() < self.model().info_column_count or drop_index.row() == 0:

            event.ignore()
            return
        
        try:
            drag_data = eval(event.mimeData().text())
            plan_id = drag_data['plan_id']
            processes = drag_data['process'].split('\n')
            
            # 드롭 위치의 날짜 가져오기
            drop_date = self.model().date_range[drop_index.column() - self.model().info_column_count]
            if isinstance(drop_date, datetime):
                drop_date = drop_date.date()
            
            # 해당 계획의 상세공정 순서 가져오기
            plan = next(plan for plan in self.model().plans if plan['id'] == plan_id)
            상세공정_raw = plan['상세Process']
            상세공정 = [p.strip() for p in 상세공정_raw.replace('\n', ' ').split('+') if p.strip()]
            
            # 드래그된 공정들을 원래 순서대로 정렬
            sorted_processes = sorted(processes, 
                                    key=lambda x: 상세공정.index(x.split(']')[-1].strip() if ']' in x else x))
            
            # 정렬된 순서대로 날짜 설정
            success = True
            for process in sorted_processes:
                # 설비 정보가 포함된 경우 제거
                clean_process = process.split(']')[-1].strip() if ']' in process else process
                if not self.model().setProcessDate(plan_id, clean_process, drop_date):
                    success = False
                    break
                    
            if success:

                event.acceptProposedAction()
            else:

                event.ignore()
                
        except Exception as e:

            event.ignore()



    def dragEnterEvent(self, event):
        if event.mimeData().hasText():

            event.acceptProposedAction()
        else:

            event.ignore()

    def dragMoveEvent(self, event):
        drop_index = self.indexAt(event.position().toPoint())
        if drop_index.isValid() and drop_index.column() >= 4:
            event.acceptProposedAction()
        else:
            event.ignore()

class ProcessSplitDialog(QDialog):
    def __init__(self, processes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("공정 분리")
        layout = QVBoxLayout()

        # 공정 선택 리스트
        self.process_list = QListWidget()
        self.process_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for process in processes:
            item = QListWidgetItem(process)
            self.process_list.addItem(item)

        layout.addWidget(QLabel("분리할 공정 선택:"))
        layout.addWidget(self.process_list)

        # 날짜 선택
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        
        # 현재 선택된 셀의 날짜 가져오기
        current_index = parent.currentIndex()
        if current_index.isValid():
            current_date = parent.model().date_range[current_index.column() - parent.model().info_column_count]
            # 다음날을 기본값으로 설정
            next_date = current_date + timedelta(days=1)
            self.date_edit.setDate(QDate(next_date.year, next_date.month, next_date.day))
        else:
            self.date_edit.setDate(QDate.currentDate())

        layout.addWidget(QLabel("이동할 날짜:"))
        layout.addWidget(self.date_edit)

        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_selected_processes(self):
        return [item.text() for item in self.process_list.selectedItems()]

    def get_target_date(self):
        return self.date_edit.date().toPyDate()


class EquipmentAssignmentDialog(QDialog):
    def __init__(self, processes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설비 할당")
        layout = QVBoxLayout()

        # productionLine 데이터 가져오기
        self.productionLine = parent.parent().productionLine
        
        # 공정 선택을 위한 리스트 위젯 (다중 선택 가능)
        self.process_list = QListWidget()
        self.process_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        # 공정 목록에 아이템 추가하고 기본적으로 모두 선택
        for process in processes.split('\n'):
            process = process.strip()
            # '[설비명]' 형식이 있다면 제거
            if ']' in process:
                process = process.split(']')[1].strip()
            item = QListWidgetItem(process)
            self.process_list.addItem(item)
            item.setSelected(True)  # 기본적으로 모두 선택
            
        layout.addWidget(QLabel("공정 선택 (Ctrl/Shift로 다중 선택):"))
        layout.addWidget(self.process_list)
        
       # 설비 타입 선택
        self.type_combo = QComboBox()
        # productionLine에서 고유한 설비 구분 값을 가져옴
        equipment_types = sorted(set(item['설비'] for item in self.productionLine))
        self.type_combo.addItems(equipment_types)
        layout.addWidget(QLabel("설비 타입:"))
        layout.addWidget(self.type_combo)
        
        # 설비 선택
        self.equipment_combo = QComboBox()
        layout.addWidget(QLabel("설비:"))
        layout.addWidget(self.equipment_combo)
        
        # all적용 체크박스
        self.apply_all_checkbox = QCheckBox("같은 날짜의 같은 공정 조합에 모두 적용")
        layout.addWidget(self.apply_all_checkbox)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.type_combo.currentTextChanged.connect(self.update_equipment_list)
        self.update_equipment_list(self.type_combo.currentText())
    
    def get_selected_processes(self):
        """선택된 공정들 반환"""
        return [item.text() for item in self.process_list.selectedItems()]
        
    def update_equipment_list(self, type_name):
        """선택된 설비 타입에 따라 설비 목록 업데이트"""
        self.equipment_combo.clear()
        # 선택된 설비 타입에 해당하는 설비들만 필터링
        equipment_names = [item['name'] for item in self.productionLine 
                         if item['설비'] == type_name and item['is_active']]
        self.equipment_combo.addItems(sorted(equipment_names))
        
    def get_selected_equipment(self):
        return self.equipment_combo.currentText()

    def apply_to_all(self):
        return self.apply_all_checkbox.isChecked()

class Wid_ProcessSchedule(  QWidget ):
    def __init__(self, parent=None, **kwargs ):
        super().__init__(parent)
        self.setWindowTitle("생산 공정 일정표")

        self.생산계획list :list[dict] = kwargs.get('생산계획list', [])
        self.휴일list :list[str] = kwargs.get('휴일list', [])
        self.dday_obj :dict = kwargs.get('dday_obj', {})
        self.공정_구분 :dict = kwargs.get('공정_구분', {})
        self.productionLine:list[dict] = kwargs.get('productionLine', [])

        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 컨트롤 패널 레이아웃
        control_panel = QHBoxLayout()

        # 테이블 뷰 설정
        self.table_view = DraggableTableView()
        self.model = ProcessScheduleModel(
            self.생산계획list, 
            self.휴일list, 
            self.dday_obj, 
            self.공정_구분,
            self.productionLine  # productionLine 전달
        )
        self.table_view.setModel(self.model)
        
        # 날짜 범위 선택
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(self.model.start_date)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(self.model.end_date)
        
        # 날짜 이동 버튼
        self.shift_left_btn = QPushButton("◀ 하루 앞으로")
        self.shift_right_btn = QPushButton("하루 뒤로 ▶")
        
        # 컨트롤 패널에 위젯 추가
        control_panel.addWidget(self.start_date_edit)
        control_panel.addWidget(self.end_date_edit)
        control_panel.addWidget(self.shift_left_btn)
        control_panel.addWidget(self.shift_right_btn)
        
        # 테이블 뷰 설정
        # self.table_view = DraggableTableView()
        # self.model = ProcessScheduleModel(생산계획list, 휴일list, dday_obj, 공정_구분)
        # self.table_view.setModel(self.model)
        
        # 시그널 연결
        self.start_date_edit.dateChanged.connect(self.update_date_range)
        self.end_date_edit.dateChanged.connect(self.update_date_range)
        self.shift_left_btn.clicked.connect(self.shift_dates_left)
        self.shift_right_btn.clicked.connect(self.shift_dates_right)
        
        # 레이아웃에 위젯 추가
        main_layout.addLayout(control_panel)
        main_layout.addWidget(self.table_view)
        
        self.setLayout(main_layout)
        
        # 컬럼 크기 조정
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.resizeColumnsToContents()

    def update_date_range(self):
        """날짜 범위 업데이트"""
        new_start = self.start_date_edit.date().toPyDate()
        new_end = self.end_date_edit.date().toPyDate()
        
        if new_start <= new_end:
            self.model.start_date = new_start
            self.model.end_date = new_end
            self.model.date_range = self.model._generate_date_range()
            # 날짜 범위가 변경될 때 합계 재계산
            self.model.daily_sums = self.model._calculate_daily_sums()
            self.model.layoutChanged.emit()
            self.table_view.resizeColumnsToContents()

    def shift_dates_left(self):
        """날짜 범위를 하루 앞으로 이동"""
        self.start_date_edit.setDate(self.start_date_edit.date().addDays(-1))
        self.end_date_edit.setDate(self.end_date_edit.date().addDays(-1))
        # 날짜 이동 후 합계 재계산
        self.model.daily_sums = self.model._calculate_daily_sums()
        self.model.layoutChanged.emit()

    def shift_dates_right(self):
        """날짜 범위를 하루 뒤로 이동"""
        self.start_date_edit.setDate(self.start_date_edit.date().addDays(1))
        self.end_date_edit.setDate(self.end_date_edit.date().addDays(1))
        # 날짜 이동 후 합계 재계산
        self.model.daily_sums = self.model._calculate_daily_sums()
        self.model.layoutChanged.emit()

    def view_selected_row(self):
        """선택된 행의 생산지시_fk 값을 반환"""
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            return None
            
        # 선택된 행 번호 가져오기 (첫 번째 선택된 셀 기준)
        row = indexes[0].row()
        if row == 0:  # 합계 행은 제외
            return None
            
        # 실제 데이터 행 인덱스 조정 (합계 행 때문에 -1)
        actual_row = row - 1
        
        # 생산지시_fk 컬럼의 인덱스 찾기
        fk_col_index = self.model.info_columns.index('생산지시_fk')
        
        # 해당 셀의 데이터 가져오기
        fk_value = self.model.plans[actual_row].get('생산지시_fk')
        
        return fk_value

    def save_changes(self):
        """변경사항 저장"""
        changes = self.model.get_changes()
        if changes:

            for change in changes:

        else:

        return changes
    
    def save_current(self):
        """현재 모든 데이터 저장"""
        current = self.model.save_current()
        if current:

            for data in current:

        else:

        return current
    
    def save_current_by_공정상세Set(self):
        """현재 모든 데이터 저장"""
        current = self.model.save_current_by_공정상세Set()
        if current:

            for data in current:

        else:

        return current

if __name__ == '__main__':
    app = QApplication([])
    window = Wid_ProcessSchedule()
    window.show()
    app.exec()

