# GKeS_api

자율주행 차량에서 수집된 비정상 주행 데이터를 클라우드에 저장하고 검색하기 위한 FastAPI 기반 API 서버입니다.
주행 영상, 썸네일, 메타데이터, 경로 정보, ROS bag 파일을 하나의 데이터 패키지로 관리하며, 웹 서비스에서 필요한 필터링과 다운로드 기능을 제공합니다.

## 주요 기능

- 주행 데이터 패키지 및 ZIP 업로드 API
- 주행 환경, 원인, 도로 조건 기반 검색/필터 API

## 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 사사

본 연구는 과학기술정보통신부 및 정보통신기획평가원의 자율주행기술개발혁신사업의 지원을 받아 수행된 연구임 (RS-2023-00232046, 비정상 주행 데이터 전송을 통한 클라우드 기반 원인 분석 기술 개발).

This work was partly supported by Institute of Information & communications Technology Planning & Evaluation (IITP) grant funded by the Korea government(MSIT) (No.2023-00232046, Development of cloud-based cause analysis technology by transmission of abnormal driving data)
