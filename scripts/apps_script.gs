/**
 * 배관매니저 Google Apps Script
 * ─────────────────────────────────────────────
 * GET/POST 모두 처리 (URLSearchParams 방식)
 * 상담접수 시트 컬럼: 날짜 | 이름 | 전화번호 | 문의내역 | 출처 | 페이지URL | 접수시간
 *
 * 배포: 확장 프로그램 → Apps Script → 새 배포 → 웹 앱
 *       실행 권한: 나, 액세스 권한: 모든 사용자
 * ─────────────────────────────────────────────
 */

function doGet(e) {
  return handleRequest(e);
}

function doPost(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    // URL 파라미터 우선 (GET 또는 POST+쿼리스트링)
    let data = {};
    if (e && e.parameter && Object.keys(e.parameter).length > 0) {
      data = e.parameter;
    } else if (e && e.postData && e.postData.contents) {
      try { data = JSON.parse(e.postData.contents); } catch (_) {}
    }

    if (data.type === 'pageview') {
      recordVisit(ss, data);
    } else {
      recordInquiry(ss, data);
    }

    return ContentService
      .createTextOutput(JSON.stringify({ result: 'ok' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ result: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ── 상담접수 기록 ────────────────────────────────────────────────────────────
function recordInquiry(ss, data) {
  const SHEET = '상담접수';
  let sheet = ss.getSheetByName(SHEET);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET);
    const header = ['날짜', '이름', '전화번호', '문의내역', '주소', '출처', '페이지URL', '접수시간'];
    sheet.appendRow(header);
    sheet.getRange(1, 1, 1, header.length)
      .setFontWeight('bold')
      .setBackground('#1565C0')
      .setFontColor('#ffffff');
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 100);
    sheet.setColumnWidth(2, 100);
    sheet.setColumnWidth(3, 130);
    sheet.setColumnWidth(4, 220);
    sheet.setColumnWidth(5, 160);
    sheet.setColumnWidth(6, 300);
    sheet.setColumnWidth(7, 180);
  } else {
    // 기존 시트에 '주소' 컬럼이 없으면 5번째 위치에 삽입
    const lastCol = sheet.getLastColumn();
    const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
    if (!headers.includes('주소')) {
      sheet.insertColumnAfter(4);
      sheet.getRange(1, 5).setValue('주소')
        .setFontWeight('bold')
        .setBackground('#1565C0')
        .setFontColor('#ffffff');
      sheet.setColumnWidth(5, 160);
    }
  }

  const now       = new Date();
  const date      = data.date      || now.toISOString().slice(0, 10);
  const name      = data.name      || '';
  const phone     = data.phone     || '';
  const inquiry   = data.inquiry   || data.content || '';
  const sido      = data.sido      || '';
  const sigungu   = data.sigungu   || '';
  const address   = [sido, sigungu].filter(Boolean).join(' ') || data.address || '';
  const source    = data.source    || data.site_url || '';
  const pageUrl   = data.page_url  || '';
  const timestamp = data.timestamp || now.toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' });

  sheet.appendRow([date, name, phone, inquiry, address, source, pageUrl, timestamp]);

  // 이메일 알림
  try {
    MailApp.sendEmail({
      to: 'woongdamchoi@gmail.com',
      subject: '[하수구접수] ' + name + ' / ' + phone,
      body: [
        '새 하수구/배관 상담이 접수되었습니다.',
        '',
        '이름: ' + name,
        '전화번호: ' + phone,
        '주소: ' + address,
        '문의내역: ' + inquiry,
        '출처: ' + source,
        '페이지: ' + pageUrl,
        '접수시간: ' + timestamp,
      ].join('\n'),
    });
  } catch (_) {}
}

// ── 방문자 카운트 기록 ────────────────────────────────────────────────────────
function recordVisit(ss, data) {
  const SHEET = '방문자';
  let sheet = ss.getSheetByName(SHEET);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET);
    const header = ['날짜', '방문자수'];
    sheet.appendRow(header);
    sheet.getRange(1, 1, 1, header.length)
      .setFontWeight('bold')
      .setBackground('#2E7D32')
      .setFontColor('#ffffff');
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 110);
    sheet.setColumnWidth(2, 100);
  }

  const today   = data.date || new Date().toISOString().slice(0, 10);
  const lastRow = sheet.getLastRow();

  if (lastRow >= 2) {
    const dateVals = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (let i = dateVals.length - 1; i >= 0; i--) {
      if (dateVals[i][0] === today) {
        const cell = sheet.getRange(i + 2, 2);
        cell.setValue((cell.getValue() || 0) + 1);
        return;
      }
    }
  }

  sheet.appendRow([today, 1]);
}
