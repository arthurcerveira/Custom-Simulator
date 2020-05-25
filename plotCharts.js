const hAxisOptions = {
  slantedText: true,
  slantedTextAngle: 60,
};

function blockSizesAdopted() {
  const sheetName = "Block-Sizes-Adopted";

  const sheet = SpreadsheetApp.getActive().getSheetByName(sheetName);
  const data = sheet.getDataRange().getValues();

  for (var index = 1; index < data.length; index = index + 5) {
    var rangeString = sheetName + "!C" + index + ":AD" + (index + 4);
    var range = sheet.getRange(rangeString);

    var video = data[index][0];
    var cfg = data[index][1];

    var title = video + " - " + cfg;

    var columnChartBuilder = sheet.newChart().asColumnChart();

    var chart = columnChartBuilder
      .setTitle(title)
      .addRange(range)
      .setPosition(5 + index * 4, 3, 0, 0)
      .setTransposeRowsAndColumns(true)
      .setNumHeaders(1)
      .setOption("hAxis", hAxisOptions)
      .build();

    sheet.insertChart(chart);
  }
}

function memoryAccessPerBlockSize() {
  const sheetName = "Mem-Access-Per-Block-Size";

  const sheet = SpreadsheetApp.getActive().getSheetByName(sheetName);
  const data = sheet.getDataRange().getValues();

  for (var index = 1; index < data.length; index = index + 5) {
    var rangeString = sheetName + "!I" + index + ":AN" + (index + 4);
    var range = sheet.getRange(rangeString);

    var video = data[index][2];
    var cfg = data[index][1];

    var title = video + " - " + cfg;

    var columnChartBuilder = sheet.newChart().asColumnChart();

    var chart = columnChartBuilder
      .setTitle(title)
      .addRange(range)
      .setPosition(2 + index * 4, 3, 0, 0)
      .setTransposeRowsAndColumns(true)
      .setNumHeaders(1)
      .setOption("hAxis", hAxisOptions)
      .build();

    sheet.insertChart(chart);
  }
}

function allBlockSizesAccessed() {
  const sheetName = "All-Block-Sizes-Access";

  const sheet = SpreadsheetApp.getActive().getSheetByName(sheetName);
  const data = sheet.getDataRange().getValues();

  for (var index = 1; index < data.length; index = index + 5) {
    var rangeString = sheetName + "!I" + index + ":AN" + (index + 4);
    var range = sheet.getRange(rangeString);

    var video = data[index][2];
    var cfg = data[index][1];

    var title = video + " - " + cfg;

    var columnChartBuilder = sheet.newChart().asColumnChart();

    var chart = columnChartBuilder
      .setTitle(title)
      .addRange(range)
      .setPosition(2 + index * 4, 3, 0, 0)
      .setTransposeRowsAndColumns(true)
      .setNumHeaders(1)
      .setOption("hAxis", hAxisOptions)
      .build();

    sheet.insertChart(chart);
  }
}
