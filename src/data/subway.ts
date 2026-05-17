// src/data/subway.ts
// 시군구별 가장 가까운 지하철역 정보 (region.csv의 시군구 컬럼명과 일치)
// 역명 클릭 시 네이버지도 검색 링크로 연결됩니다.

export interface StationInfo {
  name:    string;  // 역명 (e.g. '강남역')
  line:    string;  // 호선 (e.g. '2호선' | '2·8호선')
  addr:    string;  // 역 주소
  naverUrl: string; // 네이버지도 검색 URL
}

function naverStation(query: string) {
  return `https://map.naver.com/v5/search/${encodeURIComponent(query)}`;
}

// ──────────────────────────────────────────────────────────────────────────────
// 서울특별시 (시군구 = 구 이름, '구' 미포함)
// ──────────────────────────────────────────────────────────────────────────────
export const SUBWAY: Record<string, StationInfo> = {
  // 서울
  '강남':   { name: '강남역',             line: '2호선',         addr: '서울 강남구 강남대로 396',           naverUrl: naverStation('강남역') },
  '강동':   { name: '천호역',             line: '5·8호선',       addr: '서울 강동구 천호대로 1053',          naverUrl: naverStation('천호역') },
  '강북':   { name: '수유역',             line: '4호선',         addr: '서울 강북구 도봉로 328',             naverUrl: naverStation('수유역') },
  '강서':   { name: '발산역',             line: '5호선',         addr: '서울 강서구 공항대로 지하 238',      naverUrl: naverStation('발산역') },
  '관악':   { name: '신림역',             line: '2호선',         addr: '서울 관악구 신림로 지하 329',        naverUrl: naverStation('신림역') },
  '광진':   { name: '건대입구역',         line: '2·7호선',       addr: '서울 광진구 능동로 217',             naverUrl: naverStation('건대입구역') },
  '구로':   { name: '구로디지털단지역',   line: '2호선',         addr: '서울 구로구 디지털로26길 5',         naverUrl: naverStation('구로디지털단지역') },
  '금천':   { name: '금천구청역',         line: '1호선',         addr: '서울 금천구 시흥대로73길 70',        naverUrl: naverStation('금천구청역') },
  '노원':   { name: '노원역',             line: '4·7호선',       addr: '서울 노원구 노원로 지하 283',        naverUrl: naverStation('노원역') },
  '도봉':   { name: '도봉산역',           line: '1·7호선',       addr: '서울 도봉구 삼양로 385',             naverUrl: naverStation('도봉산역') },
  '동대문': { name: '동대문역사문화공원역', line: '2·4·5호선',   addr: '서울 중구 을지로 264 지하',          naverUrl: naverStation('동대문역사문화공원역') },
  '동작':   { name: '사당역',             line: '2·4호선',       addr: '서울 동작구 동작대로 195',           naverUrl: naverStation('사당역') },
  '마포':   { name: '홍대입구역',         line: '2호선·공항철도', addr: '서울 마포구 양화로 160 지하',       naverUrl: naverStation('홍대입구역') },
  '서대문': { name: '홍제역',             line: '3호선',         addr: '서울 서대문구 통일로 494 지하',      naverUrl: naverStation('홍제역') },
  '서초':   { name: '교대역',             line: '2·3호선',       addr: '서울 서초구 강남대로 210 지하',      naverUrl: naverStation('교대역') },
  '성동':   { name: '왕십리역',           line: '2·5호선',       addr: '서울 성동구 왕십리로 지하 270',      naverUrl: naverStation('왕십리역') },
  '성북':   { name: '길음역',             line: '4호선',         addr: '서울 성북구 솔샘로2길 지하 29',      naverUrl: naverStation('길음역') },
  '송파':   { name: '잠실역',             line: '2·8호선',       addr: '서울 송파구 올림픽로 지하 265',      naverUrl: naverStation('잠실역') },
  '양천':   { name: '목동역',             line: '5호선',         addr: '서울 양천구 목동동로 101',           naverUrl: naverStation('목동역') },
  '영등포': { name: '영등포역',           line: '1호선',         addr: '서울 영등포구 경인로 지하 846',      naverUrl: naverStation('영등포역') },
  '용산':   { name: '용산역',             line: '1호선·경의중앙선', addr: '서울 용산구 한강대로23길 55',    naverUrl: naverStation('용산역') },
  '은평':   { name: '연신내역',           line: '3·6호선',       addr: '서울 은평구 갈현로 지하 395',        naverUrl: naverStation('연신내역') },
  '종로':   { name: '종각역',             line: '1호선',         addr: '서울 종로구 종로 지하 51',           naverUrl: naverStation('종각역') },
  '중구':   { name: '을지로입구역',       line: '2호선',         addr: '서울 중구 을지로 지하 30',           naverUrl: naverStation('을지로입구역') },
  '중랑':   { name: '상봉역',             line: '7호선·경의중앙선', addr: '서울 중랑구 망우로 317',         naverUrl: naverStation('상봉역') },

  // ────────────────────────────────────────────────────────────────────────────
  // 경기도 (시군구 = 구/시/군 이름)
  // ────────────────────────────────────────────────────────────────────────────

  // 수원시 4개 구
  '장안':   { name: '수원역',     line: '1호선',         addr: '경기 수원시 팔달구 덕영대로 924',       naverUrl: naverStation('수원역') },
  '권선':   { name: '수원역',     line: '1호선',         addr: '경기 수원시 팔달구 덕영대로 924',       naverUrl: naverStation('수원역') },
  '팔달':   { name: '수원역',     line: '1호선',         addr: '경기 수원시 팔달구 덕영대로 924',       naverUrl: naverStation('수원역') },
  '영통':   { name: '영통역',     line: '수인분당선',    addr: '경기 수원시 영통구 영통로 지하 176',    naverUrl: naverStation('영통역') },

  // 성남시 3개 구
  '수정':   { name: '모란역',     line: '8호선·수인분당선', addr: '경기 성남시 중원구 성남대로 지하 1217', naverUrl: naverStation('모란역') },
  '중원':   { name: '모란역',     line: '8호선·수인분당선', addr: '경기 성남시 중원구 성남대로 지하 1217', naverUrl: naverStation('모란역') },
  '분당':   { name: '서현역',     line: '수인분당선',    addr: '경기 성남시 분당구 분당로 지하 218',    naverUrl: naverStation('서현역') },

  // 안양시 2개 구
  '만안':   { name: '안양역',     line: '1호선',         addr: '경기 안양시 만안구 안양역로 1',         naverUrl: naverStation('안양역') },
  '동안':   { name: '평촌역',     line: '1호선',         addr: '경기 안양시 동안구 평촌대로 지하 208',  naverUrl: naverStation('평촌역') },

  // 부천시 3개 구
  '원미':   { name: '부천역',     line: '1호선',         addr: '경기 부천시 부일로 지하 14',            naverUrl: naverStation('부천역') },
  '소사':   { name: '소사역',     line: '1호선·서해선',  addr: '경기 부천시 소사로 지하 184',           naverUrl: naverStation('소사역') },
  '오정':   { name: '부천역',     line: '1호선',         addr: '경기 부천시 부일로 지하 14',            naverUrl: naverStation('부천역') },

  // 용인시 3개 구
  '처인':   { name: '에버라인용인역', line: '에버라인',  addr: '경기 용인시 처인구 중부대로 1199',      naverUrl: naverStation('에버라인용인역') },
  '기흥':   { name: '기흥역',     line: '수인분당선·에버라인', addr: '경기 용인시 기흥구 강남로 지하 27', naverUrl: naverStation('기흥역') },
  '수지':   { name: '수지구청역', line: '수인분당선',    addr: '경기 용인시 수지구 포은대로 지하 474',  naverUrl: naverStation('수지구청역') },

  // 고양시 3개 구
  '덕양':   { name: '화정역',     line: '3호선',         addr: '경기 고양시 덕양구 화중로 지하 86',     naverUrl: naverStation('화정역') },
  '일산동': { name: '백석역',     line: '3호선',         addr: '경기 고양시 일산동구 백석로 지하 167',  naverUrl: naverStation('백석역') },
  '일산서': { name: '주엽역',     line: '3호선',         addr: '경기 고양시 일산서구 주엽로 지하 64',   naverUrl: naverStation('주엽역') },

  // 안산시 2개 구
  '단원':   { name: '안산역',     line: '4호선',         addr: '경기 안산시 단원구 화랑로 지하 406',    naverUrl: naverStation('안산역') },
  '상록':   { name: '상록수역',   line: '4호선',         addr: '경기 안산시 상록구 사동로 지하 123',    naverUrl: naverStation('상록수역') },

  // 기타 시/군
  '화성':       { name: '병점역',       line: '1호선',        addr: '경기 화성시 병점중앙로 지하 17',         naverUrl: naverStation('병점역') },
  '남양주':     { name: '마석역',       line: '경춘선',       addr: '경기 남양주시 화도읍 마석로 42',         naverUrl: naverStation('마석역') },
  '의정부':     { name: '의정부역',     line: '1호선·경전철', addr: '경기 의정부시 의정부로 55',              naverUrl: naverStation('의정부역') },
  '광명':       { name: '광명역',       line: 'KTX·1호선',    addr: '경기 광명시 일직로 1',                   naverUrl: naverStation('광명역') },
  '군포':       { name: '군포역',       line: '1호선',        addr: '경기 군포시 군포로 28',                  naverUrl: naverStation('군포역') },
  '시흥':       { name: '시흥시청역',   line: '서해선',       addr: '경기 시흥시 시청로 지하 10',             naverUrl: naverStation('시흥시청역') },
  '평택':       { name: '평택역',       line: '1호선',        addr: '경기 평택시 평택로 12',                  naverUrl: naverStation('평택역') },
  '파주':       { name: '운정역',       line: '경의중앙선',   addr: '경기 파주시 운정로 지하 176',            naverUrl: naverStation('운정역') },
  '김포':       { name: '구래역',       line: '김포골드라인', addr: '경기 김포시 김포한강4로 지하 185',       naverUrl: naverStation('구래역') },
  '의왕':       { name: '의왕역',       line: '1호선',        addr: '경기 의왕시 철도박물관로 142',           naverUrl: naverStation('의왕역') },
  '하남':       { name: '하남풍산역',   line: '5호선',        addr: '경기 하남시 풍산로 302',                 naverUrl: naverStation('하남풍산역') },
  '경기광주':   { name: '경기광주역',   line: '경강선',       addr: '경기 광주시 경충대로 940',               naverUrl: naverStation('경기광주역') },
  '이천':       { name: '이천역',       line: '경강선',       addr: '경기 이천시 이천대로 2450',              naverUrl: naverStation('이천역') },
  '여주':       { name: '여주역',       line: '경강선',       addr: '경기 여주시 현충로 66',                  naverUrl: naverStation('여주역') },
  '오산':       { name: '오산역',       line: '1호선',        addr: '경기 오산시 오산로 239',                 naverUrl: naverStation('오산역') },
  '양평':       { name: '양평역',       line: '경의중앙선',   addr: '경기 양평군 양평읍 양평로 지하 162',     naverUrl: naverStation('양평역') },
  '동두천':     { name: '동두천역',     line: '1호선',        addr: '경기 동두천시 중앙로 289',               naverUrl: naverStation('동두천역') },
  '양주':       { name: '양주역',       line: '1호선',        addr: '경기 양주시 부흥로 지하 1780',           naverUrl: naverStation('양주역') },
  '구리':       { name: '구리역',       line: '경의중앙선',   addr: '경기 구리시 경춘로 지하 220',            naverUrl: naverStation('구리역') },
  '과천':       { name: '과천역',       line: '4호선',        addr: '경기 과천시 별양상가2로 지하 18',        naverUrl: naverStation('과천역') },
  '안성':       { name: '평택역',       line: '1호선 (인근)', addr: '경기 평택시 평택로 12',                  naverUrl: naverStation('안성 지하철역') },
  '포천':       { name: '의정부역',     line: '1호선 (인근)', addr: '경기 의정부시 의정부로 55',              naverUrl: naverStation('포천 지하철역') },
  '가평':       { name: '가평역',       line: '경춘선',       addr: '경기 가평군 가평읍 가평로 122',          naverUrl: naverStation('가평역') },
  '연천':       { name: '전곡역',       line: '경원선',       addr: '경기 연천군 전곡읍 전곡로 169',          naverUrl: naverStation('전곡역') },
};

/** 시군구명으로 지하철역 정보 조회. 없으면 Naver 검색 URL 반환 */
export function getStation(sigungu: string): StationInfo {
  return (
    SUBWAY[sigungu] ?? {
      name:     sigungu + ' 인근 지하철역',
      line:     '검색',
      addr:     '',
      naverUrl: `https://map.naver.com/v5/search/${encodeURIComponent(sigungu + ' 지하철역')}`,
    }
  );
}
