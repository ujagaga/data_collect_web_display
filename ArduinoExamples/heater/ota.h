#ifndef OTAU_H_
#define OTAU_H_

#define OTA_PORT                        (9999)
#define DEVICE_NAME                     "Grejalica"

extern void OTA_init(void);
extern void OTA_process(void);
extern bool OTA_updateInProgress(void);

#endif
