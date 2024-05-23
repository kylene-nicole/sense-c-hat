
//#include "stdafx.h"
#include "QMI8658.h"

#define QMI8658_SLAVE_ADDR_L 0x6a
#define QMI8658_SLAVE_ADDR_H 0x6b
#define QMI8658_printf printf

#define QMI8658_UINT_MG_DPS
int QMI8658_dev;
IMU_ST_SENSOR_DATA gstGyroOffset ={0,0,0}; 
IMU_ST_SENSOR_DATA gstAccOffset ={0,0,0}; 
enum
{
	AXIS_X = 0,
	AXIS_Y = 1,
	AXIS_Z = 2,

	AXIS_TOTAL
};

typedef struct
{
	short sign[AXIS_TOTAL];
	unsigned short map[AXIS_TOTAL];
} qst_imu_layout;

static unsigned short acc_lsb_div = 0;
static unsigned short gyro_lsb_div = 0;
static unsigned short ae_q_lsb_div = (1 << 14);
static unsigned short ae_v_lsb_div = (1 << 10);
static unsigned int imu_timestamp = 0;
static struct QMI8658Config QMI8658_config;
static unsigned char QMI8658_slave_addr = QMI8658_SLAVE_ADDR_H;

unsigned char QMI8658_write_reg(unsigned char reg, unsigned char value)
{
	char wbuf[2]={reg, value};
	write(QMI8658_dev, wbuf, 2);
	return 0;
}

unsigned char QMI8658_read_reg(unsigned char reg, unsigned char *buf, unsigned short len)
{

	uint8_t temp[1] = {reg};
	write(QMI8658_dev,temp,1);
	read(QMI8658_dev,buf, len);
	return 0;
}


void QMI8658_CalAvgValue(uint8_t *pIndex, int16_t *pAvgBuffer, int16_t InVal, int32_t *pOutVal)
{ 
  uint8_t i;
  
  *(pAvgBuffer + ((*pIndex) ++)) = InVal;
    *pIndex &= 0x07;
    
    *pOutVal = 0;
  for(i = 0; i < 8; i ++) 
    {
      *pOutVal += *(pAvgBuffer + i);
    }
    *pOutVal >>= 3;
}

void QMI8658_config_acc(enum QMI8658_AccRange range, enum QMI8658_AccOdr odr, enum QMI8658_LpfConfig lpfEnable, enum QMI8658_StConfig stEnable)
{
	unsigned char ctl_dada;

	switch (range)
	{
	case QMI8658AccRange_2g:
		acc_lsb_div = (1 << 14);
		break;
	case QMI8658AccRange_4g:
		acc_lsb_div = (1 << 13);
		break;
	case QMI8658AccRange_8g:
		acc_lsb_div = (1 << 12);
		break;
	case QMI8658AccRange_16g:
		acc_lsb_div = (1 << 11);
		break;
	default:
		range = QMI8658AccRange_8g;
		acc_lsb_div = (1 << 12);
	}
	if (stEnable == QMI8658St_Enable)
		ctl_dada = (unsigned char)range | (unsigned char)odr | 0x80;
	else
		ctl_dada = (unsigned char)range | (unsigned char)odr;
	
	QMI8658_write_reg(QMI8658Register_Ctrl2, ctl_dada);
	// set LPF & HPF
	QMI8658_read_reg(QMI8658Register_Ctrl5, &ctl_dada, 1);
	ctl_dada &= 0xf0;
	if (lpfEnable == QMI8658Lpf_Enable)
	{
		ctl_dada |= A_LSP_MODE_3;
		ctl_dada |= 0x01;
	}
	else
	{
		ctl_dada &= ~0x01;
	}
	ctl_dada = 0x00;
	QMI8658_write_reg(QMI8658Register_Ctrl5, ctl_dada);
	// set LPF & HPF
}

void QMI8658_config_gyro(enum QMI8658_GyrRange range, enum QMI8658_GyrOdr odr, enum QMI8658_LpfConfig lpfEnable, enum QMI8658_StConfig stEnable)
{
	// Set the CTRL3 register to configure dynamic range and ODR
	unsigned char ctl_dada;

	// Store the scale factor for use when processing raw data
	switch (range)
	{
	case QMI8658GyrRange_16dps:
		gyro_lsb_div = 2048;
		break;
	case QMI8658GyrRange_32dps:
		gyro_lsb_div = 1024;
		break;
	case QMI8658GyrRange_64dps:
		gyro_lsb_div = 512;
		break;
	case QMI8658GyrRange_128dps:
		gyro_lsb_div = 256;
		break;
	case QMI8658GyrRange_256dps:
		gyro_lsb_div = 128;
		break;
	case QMI8658GyrRange_512dps:
		gyro_lsb_div = 64;
		break;
	case QMI8658GyrRange_1024dps:
		gyro_lsb_div = 32;
		break;
	case QMI8658GyrRange_2048dps:
		gyro_lsb_div = 16;
		break;
	default:
		range = QMI8658GyrRange_512dps;
		gyro_lsb_div = 64;
		break;
	}

	if (stEnable == QMI8658St_Enable)
		ctl_dada = (unsigned char)range | (unsigned char)odr | 0x80;
	else
		ctl_dada = (unsigned char)range | (unsigned char)odr;
	QMI8658_write_reg(QMI8658Register_Ctrl3, ctl_dada);

	// Conversion from degrees/s to rad/s if necessary
	// set LPF & HPF
	QMI8658_read_reg(QMI8658Register_Ctrl5, &ctl_dada, 1);
	ctl_dada &= 0x0f;
	if (lpfEnable == QMI8658Lpf_Enable)
	{
		ctl_dada |= G_LSP_MODE_3;
		ctl_dada |= 0x10;
	}
	else
	{
		ctl_dada &= ~0x10;
	}
	ctl_dada = 0x00;
	QMI8658_write_reg(QMI8658Register_Ctrl5, ctl_dada);
	// set LPF & HPF
}

void QMI8658_config_mag(enum QMI8658_MagDev device, enum QMI8658_MagOdr odr)
{
	QMI8658_write_reg(QMI8658Register_Ctrl4, device | odr);
}

void QMI8658_config_ae(enum QMI8658_AeOdr odr)
{
	// QMI8658_config_acc(QMI8658AccRange_8g, AccOdr_1000Hz, Lpf_Enable, St_Enable);
	// QMI8658_config_gyro(QMI8658GyrRange_2048dps, GyrOdr_1000Hz, Lpf_Enable, St_Enable);
	QMI8658_config_acc(QMI8658_config.accRange, QMI8658_config.accOdr, QMI8658Lpf_Enable, QMI8658St_Disable);
	QMI8658_config_gyro(QMI8658_config.gyrRange, QMI8658_config.gyrOdr, QMI8658Lpf_Enable, QMI8658St_Disable);
	QMI8658_config_mag(QMI8658_config.magDev, QMI8658_config.magOdr);
	QMI8658_write_reg(QMI8658Register_Ctrl6, odr);
}


float QMI8658_readTemp(void)
{
	unsigned char buf[2];
	short temp = 0;
	float temp_f = 0;

	QMI8658_read_reg(QMI8658Register_Tempearture_L, buf, 2);
	temp = ((short)buf[1] << 8) | buf[0];
	temp_f = (float)temp / 256.0f;

	return temp_f;
}

void QMI8658_read_acc_xyz(short int acc_xyz[3])
{
	unsigned char buf_reg[6];
	short int raw_acc_xyz[3];

	QMI8658_read_reg(QMI8658Register_Ax_L, buf_reg, 6); // 0x19, 25
	raw_acc_xyz[0] = (buf_reg[1] << 8) | (buf_reg[0]);
	raw_acc_xyz[1] = (buf_reg[3] << 8) | (buf_reg[2]);
	raw_acc_xyz[2] = (buf_reg[5] << 8) | (buf_reg[4]);

    acc_xyz[0] = raw_acc_xyz[0] - gstAccOffset.s16X;
    acc_xyz[1] = raw_acc_xyz[1] - gstAccOffset.s16Y;
    acc_xyz[2] = raw_acc_xyz[2] - gstAccOffset.s16Z;
	// QMI8658_printf("\r\n Acceleration: X: %d     Y: %d     Z: %d \r\n",acc_xyz[0],acc_xyz[1],acc_xyz[2]);

}
void QMI8658_read_gyro_xyz(short int gyro_xyz[3])
{
	unsigned char buf_reg[6];
	short int raw_gyro_xyz[3];

	QMI8658_read_reg(QMI8658Register_Gx_L, buf_reg, 6); // 0x1f, 31
	raw_gyro_xyz[0] = (buf_reg[1] << 8) | (buf_reg[0]);
	raw_gyro_xyz[1] = (buf_reg[3] << 8) | (buf_reg[2]);
	raw_gyro_xyz[2] = (buf_reg[5] << 8) | (buf_reg[4]);

    gyro_xyz[0] = raw_gyro_xyz[0] - gstGyroOffset.s16X;
    gyro_xyz[1] = raw_gyro_xyz[1] - gstGyroOffset.s16Y;
    gyro_xyz[2] = raw_gyro_xyz[2] - gstGyroOffset.s16Z;
	// QMI8658_printf("\r\n Gyroscope: X: %d     Y: %d     Z: %d \r\n",gyro_xyz[0], gyro_xyz[1], gyro_xyz[2]);
}


void QMI8658_enableSensors(unsigned char enableFlags)
{
	if (enableFlags & QMI8658_CONFIG_AE_ENABLE)
	{
		enableFlags |= QMI8658_CTRL7_ACC_ENABLE | QMI8658_CTRL7_GYR_ENABLE;
	}

	QMI8658_write_reg(QMI8658Register_Ctrl7, enableFlags | 0x80);
}

void QMI8658_Config_apply(struct QMI8658Config const *config)
{
	unsigned char fisSensors = config->inputSelection;

	if (fisSensors & QMI8658_CONFIG_AE_ENABLE)
	{
		QMI8658_config_ae(config->aeOdr);
	}
	else
	{
		if (config->inputSelection & QMI8658_CONFIG_ACC_ENABLE)
		{
			QMI8658_config_acc(config->accRange, config->accOdr, QMI8658Lpf_Enable, QMI8658St_Disable);
		}
		if (config->inputSelection & QMI8658_CONFIG_GYR_ENABLE)
		{
			QMI8658_config_gyro(config->gyrRange, config->gyrOdr, QMI8658Lpf_Enable, QMI8658St_Disable);
		}
	}

	if (config->inputSelection & QMI8658_CONFIG_MAG_ENABLE)
	{
		QMI8658_config_mag(config->magDev, config->magOdr);
	}
	QMI8658_enableSensors(fisSensors);
}
void QMI8658_Gyro_Acc_Offset(void)
{
  unsigned char  i;
  short int gyro[3],acc[3];
  int s32TempGx = 0, s32TempGy = 0, s32TempGz = 0;
  int s32TempAx = 0, s32TempAy = 0, s32TempAz = 0;
  for(i = 0; i < 32; i ++)
  {
    QMI8658_read_gyro_xyz(gyro);
    s32TempGx += gyro[0];
    s32TempGy += gyro[1];
    s32TempGz += gyro[2];

	QMI8658_read_acc_xyz(acc);
	s32TempAx += acc[0];
	s32TempAy += acc[1];
	s32TempAz += acc[2];
    delay(10);
  }
	gstGyroOffset.s16X = s32TempGx >> 5;
	gstGyroOffset.s16Y = s32TempGy >> 5;
	gstGyroOffset.s16Z = s32TempGz >> 5;

	gstAccOffset.s16X = s32TempAx >> 5;
	gstAccOffset.s16Y = s32TempAy >> 5;
	gstAccOffset.s16Z = (s32TempAz >> 5) - 980;
//   QMI8658_printf("\r\n Gyroscope: X: %d     Y: %d     Z: %d \r\n",gstGyroOffset.s16X, gstGyroOffset.s16Y, gstGyroOffset.s16Z);
  return;
}
unsigned char QMI8658_init(void)
{
	if (wiringPiSetup() < 0) return 0;
	QMI8658_dev = wiringPiI2CSetup(QMI8658_slave_addr);

	unsigned char QMI8658_chip_id = 0x00;
	unsigned char QMI8658_revision_id = 0x00;
	unsigned char QMI8658_slave[2] = {QMI8658_SLAVE_ADDR_L, QMI8658_SLAVE_ADDR_H};
	unsigned char iCount = 0;
	int retry = 0;
	// DEV_Delay_ms(3000);
	while (iCount < 2)
	{
		QMI8658_slave_addr = QMI8658_slave[iCount];
		retry = 0;
		while ((QMI8658_chip_id != 0x05) && (retry++ < 5))
		{
			QMI8658_read_reg(QMI8658Register_WhoAmI, &QMI8658_chip_id, 1);
			QMI8658_printf("QMI8658Register_WhoAmI = 0x%x\n", QMI8658_chip_id);
		}
		if (QMI8658_chip_id == 0x05)
		{
			break;
		}
		iCount++;
	}
	QMI8658_read_reg(QMI8658Register_Revision, &QMI8658_revision_id, 1);
	if (QMI8658_chip_id == 0x05)
	{
		QMI8658_printf("QMI8658_init slave=0x%x  QMI8658Register_WhoAmI=0x%x 0x%x\n", QMI8658_slave_addr, QMI8658_chip_id, QMI8658_revision_id);
		QMI8658_write_reg(QMI8658Register_Ctrl1, 0x60);
		QMI8658_config.inputSelection = QMI8658_CONFIG_ACCGYR_ENABLE; // QMI8658_CONFIG_ACCGYR_ENABLE;
		QMI8658_config.accRange = QMI8658AccRange_2g;
		QMI8658_config.accOdr = QMI8658AccOdr_1000Hz;
		QMI8658_config.gyrRange = QMI8658GyrRange_1024dps; //   QMI8658GyrRange_512dps
		QMI8658_config.gyrOdr = QMI8658GyrOdr_1000Hz;
		QMI8658_config.magOdr = QMI8658MagOdr_125Hz;
		QMI8658_config.magDev = MagDev_AKM09918;
		QMI8658_config.aeOdr = QMI8658AeOdr_128Hz;

		QMI8658_Config_apply(&QMI8658_config);
		if (1)
		{
			unsigned char read_data = 0x00;
			QMI8658_read_reg(QMI8658Register_Ctrl1, &read_data, 1);
			QMI8658_printf("QMI8658Register_Ctrl1=0x%x \n", read_data);
			QMI8658_read_reg(QMI8658Register_Ctrl2, &read_data, 1);
			QMI8658_printf("QMI8658Register_Ctrl2=0x%x \n", read_data);
			QMI8658_read_reg(QMI8658Register_Ctrl3, &read_data, 1);
			QMI8658_printf("QMI8658Register_Ctrl3=0x%x \n", read_data);
			QMI8658_read_reg(QMI8658Register_Ctrl4, &read_data, 1);
			QMI8658_printf("QMI8658Register_Ctrl4=0x%x \n", read_data);
			QMI8658_read_reg(QMI8658Register_Ctrl5, &read_data, 1);
			QMI8658_printf("QMI8658Register_Ctrl5=0x%x \n", read_data);
			QMI8658_read_reg(QMI8658Register_Ctrl6, &read_data, 1);
			QMI8658_printf("QMI8658Register_Ctrl6=0x%x \n", read_data);
			QMI8658_read_reg(QMI8658Register_Ctrl7, &read_data, 1);
			QMI8658_printf("QMI8658Register_Ctrl7=0x%x \n", read_data);
		}
		//		QMI8658_set_layout(2);
		QMI8658_Gyro_Acc_Offset();
		return 1;
	}
	else
	{
		QMI8658_printf("QMI8658_init fail\n");
		QMI8658_chip_id = 0;
		return 0;
	}
	// return QMI8658_chip_id;
}
