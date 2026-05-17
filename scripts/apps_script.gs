/**
 * 배관매니저 Google Apps Script
 * ─────────────────────────────────────────────
 * POST 요청 처리:
 *   type = 'inquiry'  → "상담접수" 시트에 기록
 *   type = 'pageview' → "방문자"   시트에 기록 (날짜별 카운트)
 *
 * 배포: 확장 프로그램 → Apps Script → 새 배포 → 웹 앱
 *       실행 권한: 나, 액세스 권한: 모든 사용자
 * ─────────────────────────────────────────────
 */

function doPost(e) {
  try {
    const ss   = SpreadsheetApp.getActiveSpreadsheet();
    const raw  = (e && e.postData) ? e.postData.contents : '{}';
    const data = JSON.parse(raw);

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
    const header = ['날짜', '이름', '전화번호', '문의내역', '출처', '페이지URL', '접수시간(UTC)'];
    sheet.appendRow(header);
    sheet.getRange(1, 1, 1, header.length).setFontWeight('bold').setBackground('#1565C0').setFontColor('#ffffff');
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 100);
    sheet.setColumnWidth(3, 130);
    sheet.setColumnWidth(4, 200);
    sheet.setColumnWidth(6, 300);
  }

  const date      = data.date      || new Date().toISOString().slice(0, 10);
  const name      = data.name      || '';
  const phone     = data.phone     || '';
  const inquiry   = data.inquiry   || data.category || data.service || '';
  const source    = data.source    || '';
  const pageUrl   = data.page_url  || '';
  const timestamp = data.timestamp || new Date().toISOString();

  sheet.appendRow([date, name, phone, inquiry, source, pageUrl, timestamp]);
}

// ── 방문자 카운트 기록 (날짜별 1회 누적) ────────────────────────────────────
function recordVisit(ss, data) {
  const SHEET = '방문자';
  let sheet = ss.getSheetByName(SHEET);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET);
    const header = ['날짜', '방문자수'];
    sheet.appendRow(header);
    sheet.getRange(1, 1, 1, header.length).setFontWeight('bold').setBackground('#2E7D32').setFontColor('#ffffff');
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
