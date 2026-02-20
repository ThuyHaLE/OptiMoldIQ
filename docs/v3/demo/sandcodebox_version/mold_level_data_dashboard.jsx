import { useState, useMemo } from "react";

const RAW = {
    "machineMoldFirstRunPair":[
        {"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"NaT","14000CBR-M-001":"NaT","14000CBS-M-001":"NaT","14100CBG-M-001":"2019-01-18","14100CBR-M-001":"NaT","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"2019-01-25","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"2019-01-29","PSSC-M-001":"NaT","PSSCC-M-001":"2019-01-15","PSSCH-M-001":"NaT","PSSP-M-001":"2019-01-31","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"2019-01-30","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"NaT"},
        {"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"NaT","14000CBR-M-001":"NaT","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"2019-01-24","16200CBG-M-001":"NaT","16500CBR-M-001":"2019-01-15","17101CAF-M-002":"2019-01-22","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"NaT","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"2019-01-28","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"NaT"},{"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"NaT","14000CBR-M-001":"2019-01-12","14000CBS-M-001":"NaT","14100CBG-M-001":"2018-11-22","14100CBR-M-001":"2018-12-05","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"2019-01-14","15300CBS-M-001":"NaT","16200CBG-M-001":"2018-11-07","16500CBR-M-001":"NaT","17101CAF-M-002":"2018-11-28","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"2018-11-27","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"2018-11-01","PXNHC4-M-001":"2018-11-02","PXNHC5-M-001":"2018-11-26","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"NaT","PXNSC-M-001":"2018-11-30","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"NaT"},{"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"2019-01-08","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"2018-11-14","12004CBQ-M-002":"2018-11-03","12005CBQ-M-002":"2018-11-19","13100CAG-M-002":"NaT","13200CBS-M-001":"2018-12-14","14000CBG-M-001":"2018-11-01","14000CBQ-M-001":"NaT","14000CBR-M-001":"2019-01-14","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"2018-11-20","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"2018-12-12","PGXKB-M-001":"NaT","PGXPH42-M-001":"2019-01-03","PGXPH5-M-001":"2018-12-08","PGXPH6-M-001":"2018-12-11","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"2018-12-25","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"NaT","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"2018-11-29","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"NaT"},{"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"2019-01-16","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"NaT","14000CBR-M-001":"NaT","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"2018-11-01","15000CBR-M-001":"2018-11-15","15001CAF-M-002":"2019-01-15","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"2018-11-27","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"NaT","PSSR-M-001":"2018-11-01","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"2018-11-15","PXNLG5-M-001":"2018-11-16","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"2018-11-14","PXNSG5-M-001":"2018-11-07","YXGC-M-003":"NaT"},{"10000CBR-M-001":"NaT","10000CBS-M-001":"2018-12-05","10100CBR-M-001":"2018-12-07","10100CBS-M-001":"2018-12-01","11000CBG-M-001":"NaT","11100CBG-M-001":"2018-11-27","12000CBG-M-001":"2019-01-09","12000CBS-M-001":"2018-11-10","12001CBS-M-001":"2018-11-13","12002CBS-M-001":"2018-11-15","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"2018-12-31","13100CAG-M-002":"2018-11-01","13200CBS-M-001":"NaT","14000CBG-M-001":"2018-11-20","14000CBQ-M-001":"NaT","14000CBR-M-001":"NaT","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"2018-12-19","20101IBE-M-001":"2019-01-28","20101IBE-M-002":"2019-01-02","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"2019-01-17","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"2018-11-23","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"2019-01-08","PSPH4-M-001":"2019-01-07","PSPH5-M-001":"2018-12-17","PSSC-M-001":"2019-01-15","PSSCC-M-001":"NaT","PSSCH-M-001":"2018-11-24","PSSP-M-001":"NaT","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"2018-11-01"},{"10000CBR-M-001":"2018-11-07","10000CBS-M-001":"NaT","10100CBR-M-001":"2018-12-31","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"NaT","14000CBR-M-001":"2018-11-01","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"2018-11-06","PSSP-M-001":"NaT","PSSR-M-001":"2018-12-26","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"NaT"},{"10000CBR-M-001":"2019-01-16","10000CBS-M-001":"NaT","10100CBR-M-001":"2018-11-01","10100CBS-M-001":"2018-11-16","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"2019-01-07","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"2018-12-28","14000CBQ-M-001":"NaT","14000CBR-M-001":"NaT","14000CBS-M-001":"2019-01-03","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"2018-12-18","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"2018-12-21","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"2018-12-25","PSCR25-M-001":"NaT","PSLC-M-001":"2018-11-21","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"NaT","PSSR-M-001":"NaT","PSUC-M-001":"2018-11-20","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"2018-12-20","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"2018-12-14","YXGC-M-003":"2018-11-24"},{"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"NaT","14000CBR-M-001":"2018-11-14","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"2018-11-03","14102CAJ-M-003":"2018-11-30","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"2018-12-12","PGXCR6-M-001":"2018-11-23","PGXHC-M-001":"NaT","PGXKB-M-001":"2018-11-26","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"2018-11-27","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"NaT","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"2018-11-01"},{"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"2019-01-14","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"2018-11-01","14000CBR-M-001":"NaT","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"NaT","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"NaT","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"NaT","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"NaT","20102IBE-M-002":"NaT","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"NaT","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"NaT","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"NaT","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"NaT","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"NaT","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"NaT"},{"10000CBR-M-001":"NaT","10000CBS-M-001":"NaT","10100CBR-M-001":"NaT","10100CBS-M-001":"NaT","11000CBG-M-001":"NaT","11100CBG-M-001":"NaT","12000CBG-M-001":"NaT","12000CBS-M-001":"NaT","12001CBS-M-001":"NaT","12002CBS-M-001":"NaT","12003CBQ-M-002":"NaT","12004CBQ-M-002":"NaT","12005CBQ-M-002":"NaT","13100CAG-M-002":"NaT","13200CBS-M-001":"NaT","14000CBG-M-001":"NaT","14000CBQ-M-001":"2019-01-14","14000CBR-M-001":"NaT","14000CBS-M-001":"NaT","14100CBG-M-001":"NaT","14100CBR-M-001":"NaT","14102CAJ-M-003":"2018-11-20","15000CBR-M-001":"NaT","15001CAF-M-002":"NaT","15200CBS-M-001":"NaT","15300CBG-M-001":"2018-11-02","15300CBS-M-001":"NaT","16200CBG-M-001":"NaT","16500CBR-M-001":"2018-11-01","17101CAF-M-002":"NaT","17700CBS-M-001":"NaT","20101IBE-M-001":"NaT","20101IBE-M-002":"NaT","20102IBE-M-001":"2019-01-24","20102IBE-M-002":"2019-01-02","20400IBE-M-001":"NaT","PGXCR6-M-001":"NaT","PGXHC-M-001":"NaT","PGXKB-M-001":"NaT","PGXPH42-M-001":"NaT","PGXPH5-M-001":"2018-11-15","PGXPH6-M-001":"NaT","PGXSR-M-001":"NaT","PSCR25-M-001":"NaT","PSLC-M-001":"NaT","PSLR-M-001":"NaT","PSPH2-M-001":"NaT","PSPH4-M-001":"NaT","PSPH5-M-001":"2018-11-19","PSSC-M-001":"NaT","PSSCC-M-001":"NaT","PSSCH-M-001":"NaT","PSSP-M-001":"NaT","PSSR-M-001":"NaT","PSUC-M-001":"NaT","PXNCR2-M-001":"2019-01-23","PXNCR5-M-001":"NaT","PXNHC4-M-001":"NaT","PXNHC5-M-001":"NaT","PXNLG2-M-001":"NaT","PXNLG5-M-001":"NaT","PXNLS-M-001":"2018-11-27","PXNSC-M-001":"NaT","PXNSG2-M-001":"NaT","PXNSG5-M-001":"NaT","YXGC-M-003":"NaT"}
    ],
    "moldMachineFirstRunPair":[
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"2018-11-07","MD130S-000":"2019-01-16","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-12-05","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-12-07","MD100S-001":"2018-12-31","MD130S-000":"2018-11-01","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-12-01","MD100S-001":"NaT","MD130S-000":"2018-11-16","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"2019-01-14","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2019-01-08","J100ADS-001":"NaT","MD100S-000":"2018-11-27","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2019-01-09","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-11-10","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-11-13","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-11-15","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-11-14","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-11-03","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2019-01-07","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-11-19","J100ADS-001":"2019-01-16","MD100S-000":"2018-12-31","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-11-01","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-12-14","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-11-01","J100ADS-001":"NaT","MD100S-000":"2018-11-20","MD100S-001":"NaT","MD130S-000":"2018-12-28","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"2018-11-01","MD50S-001":"2019-01-14"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"2019-01-12","J100ADS-000":"2019-01-14","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"2018-11-01","MD130S-000":"NaT","MD130S-001":"2018-11-14","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2019-01-03","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"2019-01-18","CNS50-001":"NaT","EC50ST-000":"2018-11-22","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"2018-12-05","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"2018-11-03","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"2018-11-01","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"2018-11-30","MD50S-000":"NaT","MD50S-001":"2018-11-20"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"2018-11-15","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-11-20","J100ADS-001":"2019-01-15","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2018-12-18","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"2019-01-14","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2018-11-02"},
        {"CNS50-000":"NaT","CNS50-001":"2019-01-24","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"2019-01-25","CNS50-001":"NaT","EC50ST-000":"2018-11-07","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"2019-01-15","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2018-11-01"},
        {"CNS50-000":"NaT","CNS50-001":"2019-01-22","EC50ST-000":"2018-11-28","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-12-19","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2019-01-28","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2019-01-02","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2019-01-24"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2019-01-02"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"2018-12-12","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2019-01-17","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"2018-11-23","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-12-12","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2018-12-21","MD130S-001":"2018-11-26","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2019-01-03","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-12-08","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2018-11-15"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-12-11","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2018-12-25","MD130S-001":"2018-11-27","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-11-23","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2018-11-21","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-12-25","J100ADS-001":"2018-11-27","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2019-01-08","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2019-01-07","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"2019-01-29","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-12-17","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2018-11-19"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2019-01-15","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"2019-01-15","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-11-24","MD100S-001":"2018-11-06","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"2019-01-31","CNS50-001":"NaT","EC50ST-000":"2018-11-27","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"2018-11-01","MD100S-000":"NaT","MD100S-001":"2018-12-26","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2018-11-20","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2019-01-23"},
        {"CNS50-000":"2019-01-30","CNS50-001":"NaT","EC50ST-000":"2018-11-01","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"2019-01-28","EC50ST-000":"2018-11-02","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"2018-11-26","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"2018-11-15","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"2018-11-29","J100ADS-001":"2018-11-16","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2018-12-20","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"2018-11-27"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"2018-11-30","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"2018-11-14","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"NaT","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"2018-11-07","MD100S-000":"NaT","MD100S-001":"NaT","MD130S-000":"2018-12-14","MD130S-001":"NaT","MD50S-000":"NaT","MD50S-001":"NaT"},
        {"CNS50-000":"NaT","CNS50-001":"NaT","EC50ST-000":"NaT","J100ADS-000":"NaT","J100ADS-001":"NaT","MD100S-000":"2018-11-01","MD100S-001":"NaT","MD130S-000":"2018-11-24","MD130S-001":"2018-11-01","MD50S-000":"NaT","MD50S-001":"NaT"}
    ]
};

// ── Parse data ───────────────────────────────────────────────────────────────
const moldKeys = Object.keys(RAW.machineMoldFirstRunPair[0]);
const machineKeys = Object.keys(RAW.moldMachineFirstRunPair[0]);

// machineMoldMatrix[machineIdx][moldIdx] = date or null
const machineMoldMatrix = RAW.machineMoldFirstRunPair.map(row =>
  moldKeys.map(mold => (row[mold] !== "NaT" ? row[mold] : null))
);
// moldMachineMatrix[moldIdx][machineIdx] = date or null
const moldMachineMatrix = RAW.moldMachineFirstRunPair.map(row =>
  machineKeys.map(m => (row[m] !== "NaT" ? row[m] : null))
);

// Mold counts per machine
const machineRunCounts = machineKeys.map((_, mi) => {
  return moldMachineMatrix.reduce((s, row) => s + (row[mi] !== null ? 1 : 0), 0);
});
// Machine counts per mold
const moldRunCounts = moldKeys.map((_, di) => {
  return machineMoldMatrix.reduce((s, row) => s + (row[di] !== null ? 1 : 0), 0);
});

const totalPairs = machineMoldMatrix.reduce((s, row) => s + row.filter(v => v !== null).length, 0);

// Color scale by month
function dateColor(d) {
  if (!d) return null;
  const m = d.slice(5, 7);
  const colors = {
    "11": "#7c3aed", "12": "#2563eb", "01": "#059669",
  };
  return colors[m] || "#475569";
}

function dateDot(d) {
  if (!d) return null;
  const m = d.slice(5, 7);
  if (m === "11") return "#a78bfa";
  if (m === "12") return "#60a5fa";
  return "#34d399";
}

const MACHINE_COLORS = {
  "CNS50-000": "#a78bfa", "CNS50-001": "#c4b5fd",
  "EC50ST-000": "#34d399",
  "J100ADS-000": "#60a5fa", "J100ADS-001": "#93c5fd",
  "MD100S-000": "#f97316", "MD100S-001": "#fb923c",
  "MD130S-000": "#fbbf24", "MD130S-001": "#fcd34d",
  "MD50S-000": "#f472b6", "MD50S-001": "#f9a8d4",
};

export default function App() {
  const [view, setView] = useState("heatmap_mm"); // heatmap_mm | heatmap_mach | list
  const [hoverCell, setHoverCell] = useState(null);
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [selectedMold, setSelectedMold] = useState(null);
  const [monthFilter, setMonthFilter] = useState("all");

  // filtered cells for list view
  const listData = useMemo(() => {
    const rows = [];
    moldKeys.forEach((mold, mi) => {
      machineKeys.forEach((machine, machi) => {
        const date = moldMachineMatrix[mi][machi];
        if (!date) return;
        const m = date.slice(5, 7);
        if (monthFilter !== "all" && m !== monthFilter) return;
        rows.push({ mold, machine, date });
      });
    });
    return rows.sort((a, b) => a.date.localeCompare(b.date));
  }, [monthFilter]);

  // Stats
  const nov = listData.filter(r => r.date.slice(5,7)==="11").length;
  const dec = listData.filter(r => r.date.slice(5,7)==="12").length;
  const jan = listData.filter(r => r.date.slice(5,7)==="01").length;

  // Build heatmap: molds (rows) × machines (cols)
  const HeatmapMoldMachine = () => (
    <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: "calc(100vh - 260px)" }}>
      <table style={{ borderCollapse: "collapse", fontSize: 9 }}>
        <thead>
          <tr>
            <th style={{ padding: "4px 10px", textAlign: "left", fontSize: 8, color: "#334155", letterSpacing: "0.12em", background: "#060f1c", position: "sticky", top: 0, left: 0, zIndex: 3, borderBottom: "1px solid #1e3a5f", minWidth: 140 }}>MOLD</th>
            {machineKeys.map(m => (
              <th key={m} style={{ padding: "6px 4px", fontSize: 8, color: MACHINE_COLORS[m] || "#64748b", letterSpacing: "0.08em", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f", whiteSpace: "nowrap", minWidth: 60, textAlign: "center" }}>
                {m.replace("-", "\n")}
              </th>
            ))}
            <th style={{ padding: "6px 8px", fontSize: 8, color: "#334155", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f", whiteSpace: "nowrap" }}>TOTAL</th>
          </tr>
        </thead>
        <tbody>
          {moldKeys.map((mold, mi) => {
            const rowHasData = moldMachineMatrix[mi].some(v => v !== null);
            if (!rowHasData) return null;
            return (
              <tr key={mold} style={{ borderBottom: "1px solid #0a1929" }}>
                <td style={{
                  padding: "4px 10px", color: selectedMold === mold ? "#60a5fa" : "#64748b",
                  fontSize: 9, background: "#060f1c", position: "sticky", left: 0, zIndex: 1,
                  cursor: "pointer", whiteSpace: "nowrap", fontFamily: "'DM Mono',monospace",
                  borderRight: "1px solid #1e3a5f",
                }} onClick={() => setSelectedMold(selectedMold === mold ? null : mold)}>
                  {mold}
                </td>
                {machineKeys.map((machine, machi) => {
                  const date = moldMachineMatrix[mi][machi];
                  const color = dateDot(date);
                  const isHovered = hoverCell?.mold === mold && hoverCell?.machine === machine;
                  return (
                    <td key={machine}
                      onMouseEnter={() => setHoverCell({ mold, machine, date })}
                      onMouseLeave={() => setHoverCell(null)}
                      style={{
                        padding: "3px", textAlign: "center",
                        background: isHovered ? "#0f2040" : date ? dateColor(date) + "18" : "transparent",
                        border: isHovered ? `1px solid ${color || "#334155"}` : "1px solid transparent",
                        cursor: date ? "pointer" : "default",
                        minWidth: 56,
                      }}>
                      {date ? (
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}>
                          <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, margin: "0 auto" }} />
                          <span style={{ color, fontSize: 8, fontFamily: "'DM Mono',monospace", letterSpacing: "0.02em" }}>
                            {date.slice(5)}
                          </span>
                        </div>
                      ) : (
                        <span style={{ color: "#1e293b", fontSize: 9 }}>·</span>
                      )}
                    </td>
                  );
                })}
                <td style={{ padding: "4px 8px", textAlign: "center", color: "#475569", fontFamily: "'DM Mono',monospace", fontSize: 10, fontWeight: 500 }}>
                  {moldRunCounts[mi] > 0 ? <span style={{ color: "#60a5fa" }}>{moldRunCounts[mi]}</span> : <span style={{ color: "#1e293b" }}>0</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );

  // Heatmap: machines (rows) × molds (cols) — transposed
  const HeatmapMachMold = () => (
    <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: "calc(100vh - 260px)" }}>
      <table style={{ borderCollapse: "collapse", fontSize: 9 }}>
        <thead>
          <tr>
            <th style={{ padding: "4px 10px", textAlign: "left", fontSize: 8, color: "#334155", letterSpacing: "0.12em", background: "#060f1c", position: "sticky", top: 0, left: 0, zIndex: 3, borderBottom: "1px solid #1e3a5f", minWidth: 110 }}>MACHINE</th>
            {moldKeys.filter((_, mi) => moldRunCounts[mi] > 0).map(mold => (
              <th key={mold} style={{ padding: "6px 2px", fontSize: 7, color: "#475569", letterSpacing: "0.05em", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f", whiteSpace: "nowrap", minWidth: 52, textAlign: "center", writingMode: "vertical-rl", height: 90, verticalAlign: "bottom" }}>
                {mold}
              </th>
            ))}
            <th style={{ padding: "6px 8px", fontSize: 8, color: "#334155", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f" }}>TOTAL</th>
          </tr>
        </thead>
        <tbody>
          {machineKeys.map((machine, machi) => {
            const activeMolds = moldKeys.filter((_, mi) => moldRunCounts[mi] > 0);
            return (
              <tr key={machine} style={{ borderBottom: "1px solid #0a1929" }}>
                <td style={{
                  padding: "5px 10px", color: MACHINE_COLORS[machine] || "#64748b",
                  fontSize: 10, background: "#060f1c", position: "sticky", left: 0, zIndex: 1,
                  fontFamily: "'DM Mono',monospace", whiteSpace: "nowrap", fontWeight: 500,
                  borderRight: "1px solid #1e3a5f",
                }}>{machine}</td>
                {activeMolds.map(mold => {
                  const mi = moldKeys.indexOf(mold);
                  const date = moldMachineMatrix[mi][machi];
                  const color = dateDot(date);
                  const isHov = hoverCell?.mold === mold && hoverCell?.machine === machine;
                  return (
                    <td key={mold}
                      onMouseEnter={() => setHoverCell({ mold, machine, date })}
                      onMouseLeave={() => setHoverCell(null)}
                      style={{
                        padding: "3px", textAlign: "center",
                        background: isHov ? "#0f2040" : date ? dateColor(date) + "22" : "transparent",
                        border: isHov ? `1px solid ${color || "#334155"}` : "1px solid transparent",
                        minWidth: 50,
                      }}>
                      {date ? (
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}>
                          <div style={{ width: 7, height: 7, borderRadius: "50%", background: color }} />
                          <span style={{ color, fontSize: 7.5, fontFamily: "'DM Mono',monospace" }}>{date.slice(5)}</span>
                        </div>
                      ) : <span style={{ color: "#1e293b" }}>·</span>}
                    </td>
                  );
                })}
                <td style={{ padding: "4px 8px", textAlign: "center", fontFamily: "'DM Mono',monospace", fontSize: 10 }}>
                  <span style={{ color: machineRunCounts[machi] > 0 ? MACHINE_COLORS[machine] : "#1e293b", fontWeight: 500 }}>{machineRunCounts[machi]}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "#020b18", fontFamily: "'DM Mono','Courier New',monospace", color: "#e2e8f0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&display=swap');
        * { box-sizing: border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:4px; height:4px; }
        ::-webkit-scrollbar-track { background:#0f172a; }
        ::-webkit-scrollbar-thumb { background:#334155; border-radius:2px; }
        .pill { background:transparent; border:1px solid #1e3a5f; border-radius:4px; color:#64748b; padding:5px 12px; cursor:pointer; font-family:'DM Mono',monospace; font-size:10px; letter-spacing:0.08em; transition:all 0.15s; }
        .pill.active { background:#1d4ed8; border-color:#2563eb; color:#fff; }
        .pill:hover:not(.active) { border-color:#334155; color:#94a3b8; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)} }
        .fade-up { animation:fadeUp 0.3s ease forwards; }
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0.3} }
        .blink { animation:blink 1.6s ease-in-out infinite; }
        tr:hover td { background:#06111e !important; }
      `}</style>

      {/* HEADER */}
      <div style={{ background:"#060f1c", borderBottom:"1px solid #1e3a5f", padding:"14px 28px", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div style={{ width:3, height:34, background:"#2563eb", borderRadius:2 }} />
          <div>
            <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:22, letterSpacing:"0.12em", color:"#60a5fa" }}>MOLD · MACHINE PAIRING</div>
            <div style={{ fontSize:9, color:"#475569", letterSpacing:"0.2em" }}>FIRST RUN DATE MATRIX — INJECTION MOLDING</div>
          </div>
        </div>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <div style={{ width:7, height:7, borderRadius:"50%", background:"#22c55e", boxShadow:"0 0 8px #22c55e" }} className="blink" />
          <span style={{ fontSize:9, color:"#475569", letterSpacing:"0.1em" }}>LIVE</span>
        </div>
      </div>

      <div style={{ padding:"18px 28px" }}>
        {/* KPI */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(6,1fr)", gap:10, marginBottom:16 }} className="fade-up">
          {[
            { label:"TOTAL PAIRS", value:totalPairs, color:"#60a5fa", sub:"mold-machine runs" },
            { label:"MOLDS ACTIVE", value:moldKeys.filter((_,i)=>moldRunCounts[i]>0).length, color:"#34d399", sub:`of ${moldKeys.length} total` },
            { label:"MACHINES ACTIVE", value:machineKeys.filter((_,i)=>machineRunCounts[i]>0).length, color:"#f472b6", sub:`of ${machineKeys.length} total` },
            { label:"NOV 2018", value:RAW.moldMachineFirstRunPair.reduce((s,r)=>s+Object.values(r).filter(v=>v&&v.slice(5,7)==="11").length,0), color:"#a78bfa", sub:"first runs" },
            { label:"DEC 2018", value:RAW.moldMachineFirstRunPair.reduce((s,r)=>s+Object.values(r).filter(v=>v&&v.slice(5,7)==="12").length,0), color:"#60a5fa", sub:"first runs" },
            { label:"JAN 2019", value:RAW.moldMachineFirstRunPair.reduce((s,r)=>s+Object.values(r).filter(v=>v&&v.slice(5,7)==="01").length,0), color:"#34d399", sub:"first runs" },
          ].map(k => (
            <div key={k.label} style={{ background:"#0c1a2e", border:"1px solid #1e3a5f", borderLeft:`3px solid ${k.color}`, borderRadius:8, padding:"12px 16px" }}>
              <div style={{ fontSize:9, color:"#475569", letterSpacing:"0.12em", marginBottom:4 }}>{k.label}</div>
              <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:28, color:k.color, lineHeight:1 }}>{k.value}</div>
              <div style={{ fontSize:9, color:"#334155", marginTop:3 }}>{k.sub}</div>
            </div>
          ))}
        </div>

        {/* CONTROLS */}
        <div style={{ background:"#0c1a2e", border:"1px solid #1e3a5f", borderRadius:8, padding:"10px 14px", marginBottom:14, display:"flex", flexWrap:"wrap", gap:8, alignItems:"center" }}>
          <button className={`pill ${view==="heatmap_mach"?"active":""}`} onClick={()=>setView("heatmap_mach")}>MACHINE × MOLD</button>
          <button className={`pill ${view==="heatmap_mm"?"active":""}`} onClick={()=>setView("heatmap_mm")}>MOLD × MACHINE</button>
          <button className={`pill ${view==="list"?"active":""}`} onClick={()=>setView("list")}>LIST VIEW</button>
          {view==="list" && (
            <>
              <div style={{ width:1, height:20, background:"#1e3a5f" }} />
              {[["all","ALL"],["11","NOV"],["12","DEC"],["01","JAN"]].map(([v,l]) => (
                <button key={v} className={`pill ${monthFilter===v?"active":""}`} onClick={()=>setMonthFilter(v)}>{l}</button>
              ))}
            </>
          )}
          {/* Legend */}
          <div style={{ marginLeft:"auto", display:"flex", gap:12, alignItems:"center" }}>
            {[["#a78bfa","NOV 2018"],["#60a5fa","DEC 2018"],["#34d399","JAN 2019"]].map(([c,l]) => (
              <div key={l} style={{ display:"flex", alignItems:"center", gap:5, fontSize:9, color:"#475569" }}>
                <div style={{ width:8, height:8, borderRadius:"50%", background:c }} />
                {l}
              </div>
            ))}
          </div>
        </div>

        {/* TOOLTIP */}
        {hoverCell && hoverCell.date && (
          <div style={{ background:"#0c1a2e", border:`1px solid ${dateDot(hoverCell.date)}`, borderRadius:6, padding:"8px 14px", marginBottom:10, display:"flex", gap:20, alignItems:"center", fontSize:10 }} className="fade-up">
            <span style={{ color:"#475569", letterSpacing:"0.08em" }}>MOLD</span>
            <span style={{ color:"#93c5fd", fontWeight:500 }}>{hoverCell.mold}</span>
            <span style={{ color:"#475569" }}>×</span>
            <span style={{ color:"#475569", letterSpacing:"0.08em" }}>MACHINE</span>
            <span style={{ color:MACHINE_COLORS[hoverCell.machine]||"#64748b", fontWeight:500 }}>{hoverCell.machine}</span>
            <span style={{ color:"#475569" }}>FIRST RUN</span>
            <span style={{ color:dateDot(hoverCell.date), fontWeight:700 }}>{hoverCell.date}</span>
          </div>
        )}

        {/* VIEWS */}
        <div style={{ background:"#0c1a2e", border:"1px solid #1e3a5f", borderRadius:8, overflow:"hidden" }} className="fade-up">
          {view === "heatmap_mm" && <HeatmapMoldMachine />}
          {view === "heatmap_mach" && <HeatmapMachMold />}
          {view === "list" && (
            <div style={{ overflowY:"auto", maxHeight:"calc(100vh - 280px)" }}>
              <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
                <thead>
                  <tr>
                    {["DATE","MOLD","MACHINE","MONTH"].map(h => (
                      <th key={h} style={{ padding:"8px 14px", textAlign:"left", fontSize:8, color:"#475569", letterSpacing:"0.15em", fontWeight:500, borderBottom:"1px solid #1e3a5f", background:"#060f1c", whiteSpace:"nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {listData.map((r, i) => {
                    const color = dateDot(r.date);
                    return (
                      <tr key={i} style={{ borderBottom:"1px solid #0a1929", background:i%2===0?"transparent":"#060e1a" }}>
                        <td style={{ padding:"8px 14px", color, fontFamily:"'DM Mono',monospace", fontWeight:500 }}>{r.date}</td>
                        <td style={{ padding:"8px 14px", color:"#64748b", fontSize:10 }}>{r.mold}</td>
                        <td style={{ padding:"8px 14px", color:MACHINE_COLORS[r.machine]||"#64748b", fontWeight:500 }}>{r.machine}</td>
                        <td style={{ padding:"8px 14px" }}>
                          <span style={{ fontSize:8, padding:"2px 8px", borderRadius:3, background:color+"22", color, border:`1px solid ${color}44`, letterSpacing:"0.08em" }}>
                            {r.date.slice(0,7)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {listData.length===0 && (
                    <tr><td colSpan={4} style={{ textAlign:"center", padding:40, color:"#334155", letterSpacing:"0.1em" }}>NO DATA</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}