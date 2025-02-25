import pynvml
import numpy as np

def check_nvlink_status():
    """
    Linux 환경에서 NVLink 연결 상태를 확인하는 함수
    
    Returns:
        tuple: (nvlink_matrix, nvlink_pairs, total_bandwidth)
            - nvlink_matrix: GPU 간 NVLink 연결 상태를 나타내는 행렬
            - nvlink_pairs: NVLink로 연결된 GPU 쌍 목록
            - total_bandwidth: 각 연결의 총 대역폭 (GB/s)
    """
    # NVML 초기화
    pynvml.nvmlInit()
    
    try:
        # GPU 개수 확인
        device_count = pynvml.nvmlDeviceGetCount()
        print(f"시스템에서 발견된 GPU 개수: {device_count}")
        
        # GPU 정보 출력
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            print(f"GPU {i}: {name}")
            
            # GPU 메모리 정보 출력
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            total_mem = mem_info.total / (1024**3)  # GB 단위로 변환
            used_mem = mem_info.used / (1024**3)
            print(f"  - VRAM: 총 {total_mem:.2f} GB, 사용 중 {used_mem:.2f} GB, 사용률: {(used_mem/total_mem)*100:.1f}%")
        
        # NVLink 연결 상태를 저장할 행렬 초기화
        nvlink_matrix = np.zeros((device_count, device_count), dtype=int)
        nvlink_pairs = []
        nvlink_bandwidth = {}
        
        print("\nNVLink 연결 확인 중...")
        
        # 각 GPU에 대해 NVLink 연결 확인
        for i in range(device_count):
            handle_i = pynvml.nvmlDeviceGetHandleByIndex(i)
            
            # 이 GPU에서 사용 가능한 NVLink 수 확인
            try:
                nvlink_count = pynvml.nvmlDeviceGetNvLinkCount(handle_i)
                print(f"GPU {i}의 NVLink 수: {nvlink_count}")
                
                # 각 NVLink 상태 확인
                for link in range(nvlink_count):
                    try:
                        # NVLink 상태 확인
                        link_status = pynvml.nvmlDeviceGetNvLinkStatus(handle_i, link)
                        is_active = link_status == 0  # 0은 active를 의미
                        
                        if is_active:
                            # NVLink가 연결된 원격 GPU 찾기
                            try:
                                remote_gpu = pynvml.nvmlDeviceGetNvLinkRemotePciInfo(handle_i, link)
                                # 원격 GPU 인덱스 찾기
                                remote_idx = -1
                                for j in range(device_count):
                                    handle_j = pynvml.nvmlDeviceGetHandleByIndex(j)
                                    pci_info = pynvml.nvmlDeviceGetPciInfo(handle_j)
                                    if pci_info.busId == remote_gpu.busId:
                                        remote_idx = j
                                        break
                                
                                if remote_idx != -1 and remote_idx != i:
                                    nvlink_matrix[i, remote_idx] = 1
                                    
                                    # NVLink 버전 확인
                                    try:
                                        nvlink_version = pynvml.nvmlDeviceGetNvLinkVersion(handle_i, link)
                                        print(f"  - NVLink {link}는 GPU {i}와 GPU {remote_idx} 사이에 활성화됨 (버전: {nvlink_version})")
                                        
                                        # 중복 쌍 방지
                                        if (remote_idx, i) not in nvlink_pairs and (i, remote_idx) not in nvlink_pairs:
                                            nvlink_pairs.append((i, remote_idx))
                                            
                                            # NVLink 버전에 따른 대역폭 계산 (GB/s)
                                            if nvlink_version == 1:
                                                bandwidth = 20  # NVLink 1.0: 20 GB/s
                                            elif nvlink_version == 2:
                                                bandwidth = 25  # NVLink 2.0: 25 GB/s
                                            elif nvlink_version == 3:
                                                bandwidth = 50  # NVLink 3.0: 50 GB/s
                                            elif nvlink_version == 4:
                                                bandwidth = 100  # NVLink 4.0: 100 GB/s
                                            else:
                                                bandwidth = 0
                                                
                                            nvlink_bandwidth[(i, remote_idx)] = bandwidth
                                    except pynvml.NVMLError as e:
                                        print(f"  - GPU {i}의 NVLink {link} 버전 확인 실패: {e}")
                            except pynvml.NVMLError as e:
                                print(f"  - GPU {i}의 NVLink {link} 원격 정보 확인 실패: {e}")
                    except pynvml.NVMLError as e:
                        print(f"  - GPU {i}의 NVLink {link} 상태 확인 실패: {e}")
            except pynvml.NVMLError as e:
                print(f"GPU {i}의 NVLink 수 확인 실패: {e}")
        
        # 결과 출력
        print("\nNVLink 연결 행렬:")
        print(nvlink_matrix)
        
        if nvlink_pairs:
            print("\nNVLink로 연결된 GPU 쌍:")
            
            for pair in nvlink_pairs:
                i, j = pair
                handle_i = pynvml.nvmlDeviceGetHandleByIndex(i)
                handle_j = pynvml.nvmlDeviceGetHandleByIndex(j)
                
                info_i = pynvml.nvmlDeviceGetMemoryInfo(handle_i)
                info_j = pynvml.nvmlDeviceGetMemoryInfo(handle_j)
                
                # VRAM 합계 계산 (GB)
                combined_vram = (info_i.total + info_j.total) / (1024**3)
                
                print(f"GPU {i} <-> GPU {j} (대역폭: {nvlink_bandwidth.get(pair, 'Unknown')} GB/s, 총 VRAM: {combined_vram:.2f} GB)")
            
            # NVLink 그룹 찾기 (연결된 GPU 클러스터)
            visited = set()
            nvlink_groups = []
            
            for i in range(device_count):
                if i not in visited:
                    group = []
                    queue = [i]
                    
                    while queue:
                        node = queue.pop(0)
                        if node not in visited:
                            visited.add(node)
                            group.append(node)
                            
                            for j in range(device_count):
                                if nvlink_matrix[node, j] == 1 and j not in visited:
                                    queue.append(j)
                    
                    if len(group) > 1:  # 다른 GPU와 연결된 그룹만 포함
                        nvlink_groups.append(group)
            
            if nvlink_groups:
                print("\nNVLink로 연결된 GPU 그룹:")
                for idx, group in enumerate(nvlink_groups):
                    # 그룹 내 모든 GPU의 총 VRAM 계산
                    total_group_vram = 0
                    for gpu_idx in group:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_idx)
                        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        total_group_vram += info.total / (1024**3)
                    
                    gpu_str = ", ".join([f"GPU {g}" for g in group])
                    print(f"그룹 {idx+1}: {gpu_str} (총 VRAM: {total_group_vram:.2f} GB)")
        else:
            print("\nNVLink로 연결된 GPU가 없습니다.")
        
        return nvlink_matrix, nvlink_pairs, nvlink_bandwidth
    
    finally:
        # NVML 종료
        pynvml.nvmlShutdown()

# 간소화된 NVLink 연결 확인 함수 (위 함수에서 오류가 발생할 경우 사용)
def check_nvlink_simplified():
    """
    Linux 환경에서 NVLink 연결을 확인하는 간소화된 방법
    """
    pynvml.nvmlInit()
    
    try:
        # GPU 개수 확인
        device_count = pynvml.nvmlDeviceGetCount()
        print(f"시스템에서 발견된 GPU 개수: {device_count}")
        
        # GPU 정보 출력
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            print(f"GPU {i}: {name}")
        
        print("\nNVLink 연결 확인 (간소화된 방법):")
        
        # 각 GPU에 대한 P2P 접근 가능 여부 확인 (NVLink의 대리 지표)
        for i in range(device_count):
            handle_i = pynvml.nvmlDeviceGetHandleByIndex(i)
            
            for j in range(device_count):
                if i == j:
                    continue
                    
                handle_j = pynvml.nvmlDeviceGetHandleByIndex(j)
                
                try:
                    # P2P 접근 가능 여부 확인
                    p2p_status = pynvml.nvmlDeviceGetP2PStatus(handle_i, handle_j, 0)  # 0: P2P_STATUS_OK
                    
                    if p2p_status == 0:  # 0은 P2P가 가능함을 의미
                        info_i = pynvml.nvmlDeviceGetMemoryInfo(handle_i)
                        info_j = pynvml.nvmlDeviceGetMemoryInfo(handle_j)
                        
                        # VRAM 합계 계산 (GB)
                        combined_vram = (info_i.total + info_j.total) / (1024**3)
                        
                        print(f"GPU {i} <-> GPU {j} P2P 접근 가능 (총 VRAM: {combined_vram:.2f} GB)")
                except pynvml.NVMLError as e:
                    print(f"GPU {i} <-> GPU {j} P2P 상태 확인 실패: {e}")
    
    finally:
        pynvml.nvmlShutdown()

if __name__ == "__main__":
    try:
        print("NVLink 상태 확인 시도 중...")
        try:
            nvlink_matrix, nvlink_pairs, nvlink_bandwidth = check_nvlink_status()
        except Exception as e:
            print(f"NVLink 상태 확인 중 오류 발생: {e}")
            print("\n간소화된 방법으로 재시도합니다...\n")
            check_nvlink_simplified()
    except Exception as error:
        print(f"전체 스크립트 실행 중 오류 발생: {error}")