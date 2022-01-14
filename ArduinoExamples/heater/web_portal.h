#ifndef WEB_PORTAL_H_
#define WEB_PORTAL_H_

// Controll variable names
#define TARGET_TEMP_VAR             "Ciljna%20temperatura"
#define AUTO_MODE_VAR               "Automatska%20kontrola"
#define GROUP_VAR                   "Grejalica"

void WP_setAutoMode(bool autoModeOn);
bool WP_getAutoMode(void);
float WP_getTargetTemp(void);
void WP_sendData(void);
void WP_setCurrentTemperature(float curTemp);
void WP_readData(void);

#endif 
