function globalVariables() {
  var variables = { spreadsheetId : 'YOUR-SPREADSHEET-ID', 
                    parse_temp: 'temp', 
                    parse_humidity: 'humidity',
                    parse_homeTemp: 'hometemp',
                    parse_homeTarget: 'hometarget',
                    parse_homeHumidity: 'homehumidity',
                    parse_nestMode: 'nestmode' }; 
  return variables;
}

function doGet(e) {
  Logger.log("Running web function...")
  
  var queryString = e.queryString;
  
  var temp = getQueryStringValue(queryString, globalVariables().parse_temp);
  var humidity = getQueryStringValue(queryString, globalVariables().parse_humidity);
  var homeTemp = getQueryStringValue(queryString, globalVariables().parse_homeTemp);
  var homeTarget = getQueryStringValue(queryString, globalVariables().parse_homeTarget);
  var homeHumidity = getQueryStringValue(queryString, globalVariables().parse_homeHumidity);
  var nestMode = getQueryStringValue(queryString, globalVariables().parse_nestMode);
  
  var time = new Date();  
  var Mt = Utilities.formatDate(time, Session.getScriptTimeZone(), "MM");
  var Yr  = Utilities.formatDate(time, Session.getScriptTimeZone(), "YYYY");
  var Dy  = Utilities.formatDate(time, Session.getScriptTimeZone(), "dd");
  
  var ss = SpreadsheetApp.openById(globalVariables().spreadsheetId);
  //I have multiple tabs, this puts the data in the first tab. Change the [0] to [1] for the second tab, [2] for the third, etc
  var sheet = ss.getSheets()[0];
  
  sheet.appendRow([time, Mt, Dy, Yr, homeTemp, homeTarget, homeHumidity, nestMode, temp, humidity]);

  textOutput = ContentService.createTextOutput("Welcome to the Nest app.")

  return textOutput
}

// Utility function to fetch key values from query string
function getQueryStringValue(query, key){
  var queryParts = query.split("&");
  if(queryParts && queryParts.length > 0){
    for(var i=0; i<queryParts.length; i++){
      var k = queryParts[i].split("=")[0];
      var value = queryParts[i].split("=")[1];
      if(k == key) return value.replace('.',',');
    }
  }
}
