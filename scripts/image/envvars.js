
module.exports = function (deltaTemp, breathTemp) {
    let module = {};
    const colorMainSets = {
        0: {
            // SET 1
            "MS_01": 'rgba(255,0,255, 0.2)', //PURPLE
            "MS_02": 'rgba(228,0,255, 0.4)', //ROSA
            "MS_03": 'rgba(247,048,136, 0.3)', //PINK
            "MS_04": 'rgba(255,255,0, 0.25)', //YELLOW
            "MS_05": 'rgba(252,55,231, 0.3)', //PINK1
            "MS_06": 'rgba(169,18,255, 0.3)', //VIOLET1
        },
        1: {
            //MS 02
            //COLOURS MAINSET (MS)
            "MS_01": 'rgba(0,255,0, 0.25)', //GREEN
            "MS_02": 'rgba(12,146,0, 0.4)', //DARK GREEN
            "MS_03": 'rgba(35,255,133, 0.3)', //MINT
            "MS_04": 'rgba(255,255,0, 0.25)', //YELLOW
            "MS_05": 'rgba(118,255,208, 0.3)', //AQUA
            "MS_06": 'rgba(138,255,0, 0.3)', //NEON GREEN
        },
        2: {
            //MS 03
            //COLOURS MAINSET (MS)
            "MS_01": 'rgba(247, 33, 25, 0.3)', //RED
            "MS_02": 'rgba(227,12,80, 0.4)', //REDISH VIOLET
            "MS_03": 'rgba(255,114,0, 0.3)', //ORANGE
            "MS_04": 'rgba(255,255,0, 0.25)', //YELLOW
            "MS_05": 'rgba(138,0,0, 0.4)', //DARK RED
            "MS_06": 'rgba(255,0,0, 0.35)', //NEON RED
        },
        3: {
            //MS 04
            //COLOURS MAINSET (MS)
            "MS_01": 'rgba(0,26,214, 0.4)', //BLUE INTENSE
            "MS_02": 'rgba(24,62,250, 0.2)', //BLUE
            "MS_03": 'rgba(0,96,178, 0.25)', //L'HEURE BLEU
            "MS_04": 'rgba(255,255,0, 0.25)', //YELLOW
            "MS_05": 'rgba(0,132,255, 0.4)', //SKY BLUE
            "MS_06": 'rgba(0,255,255, 0.35)', //CYAN
        },
        4: {
            //MS 05
            //COLOURS MAINSET (MS)
            "MS_01": 'rgba(255,240,0, 0.35)', //LEMON
            "MS_02": 'rgba(255, 94,0, 0.3)', //ORANGE2
            "MS_03": 'rgba(255,192,0, 0.25)', //YELLOW WARM
            "MS_04": 'rgba(255,255,0, 0.3)', //YELLOW
            "MS_05": 'rgba(250,255,0, 0.15)', //LEMON GLACIER
            "MS_06": 'rgba(255,192,50, 0.25)', //YELLOW WARM2
        },
        5: {
            //MS 06
            //COLOURS MAINSET (MS)
            "MS_01": 'rgba(0, 111, 255, 0.35)', //BRANDEIS BLUE
            "MS_02": 'rgba(19, 244, 239, 0.35)', //FLUORESCENT BLUE
            "MS_03": 'rgba(104, 255, 0, 0.35)', //BRIGHT GREEN
            "MS_04": 'rgba(255,255,0, 0.35)', //YELLOW
            "MS_05": 'rgba(255, 95, 31, 0.35)', //CLOCKWORK ORANGE
            "MS_06": 'rgba(255, 0, 92, 0.35)', //FOLLY
        },
        6: {
            //MS 07
            //COLOURS MAINSET (MS)
            "MS_01": 'rgba(111, 111, 111, 0.35)', //GRAY1
            "MS_02": 'rgba(19, 19, 19, 0.35)', //GRAY2
            "MS_03": 'rgba(104, 104, 104, 0.35)', //GRAY3
            "MS_04": 'rgba(222,222,222, 0.35)', //GRAY4
            "MS_05": 'rgba(95, 95, 95, 0.35)', //GRAY5
            "MS_06": 'rgba(250, 250, 250, 0.35)', //GRAY6
        },
        7: {
            //MS 08
            //COLOURS MAINSET (MS)
            "MS_01": 'rgba(255,0,255, 0.2)', //PURPLE
            "MS_02": 'rgba(227,12,80, 0.4)', //REDISH VIOLET
            "MS_03": 'rgba(252,55,231, 0.2)', //PINK1
            "MS_04": 'rgba(255,255,0, 0.25)', //YELLOW
            "MS_05": 'rgba(138,0,0, 0.4)', //DARK RED
            "MS_06": 'rgba(255,0,0, 0.3)', //NEON RED
        }
    };

    const colorSubSets = {
        0: {
            //SS 01
            "TOP": 'rgba(24,62,250, 0.4)', // H2 CLOUD 006 //H2_TOP_BLUE
            "BOT": 'rgba(0,255,255, 0.2)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_CYAN
        },
        1: {
            //SS 02
            "TOP": 'rgba(0,255,255, 0.35)', // H2 CLOUD 006 //H2_TOP_CAYN
            "BOT": 'rgba(0,255,0, 0.25)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_GREEN
        },
        2: {
            //SS 03
            "TOP": 'rgba(0,255,0, 0.4)', // H2 CLOUD 006 //H2_TOP_GREEN
            "BOT": 'rgba(255,255,0, 0.25)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_YELLOW
        },
        3: {
            //SS 04
            "TOP": 'rgba(255,255,0, 0.4)', // H2 CLOUD 006 //H2_TOP_YELLOW
            "BOT": 'rgba(255, 95, 31, 0.3)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_ORANGE
        },
        4: {
            //SS 05
            "TOP": 'rgba(255, 95, 31, 0.4)', // H2 CLOUD 006 //H2_TOP_ORANGE
            "BOT": 'rgba(247, 33, 25, 0.4)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_RED
        },
        5: {
            //SS 06
            "TOP": 'rgba(247, 33, 25, 0.4)', // H2 CLOUD 006 //H2_TOP_RED
            "BOT": 'rgba(24,62,250, 0.2)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_BLUE
        },
    };

    const colorUniSets = {
        7: {
            //SS 07_08
            "TOP": 'rgba(118,255,208, 0.3)', // H2 CLOUD 006 //H2_TOP_AQUA
            "BOT": 'rgba(24,62,250, 0.4)',  // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_BLUE2
        },
        6: {
            //SS 07_07
            "TOP": 'rgba(0, 0, 0, 0.4)', // H2 CLOUD 006 //H2_TOP_BLACKY
            "BOT": 'rgba(255,255,255, 0.3)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_WHITE2
        },
        5: {
            //SS 07_06
            "TOP": 'rgba(228,0,255, 0.4)', // H2 CLOUD 006 //H2_TOP_ROSA
            "BOT": 'rgba(150,075,250, 0.4)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_PINK
        },
        4: {
            //SS 07_05
            "TOP": 'rgba(228,0,255, 0.4)', // H2 CLOUD 006 //H2_TOP_ROSA
            "BOT": 'rgba(150,075,250, 0.4)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_MAGENTA
        },
        3: {
            //SS 07_04
            "TOP": 'rgba(24,62,250, 0.4)', // H2 CLOUD 006 //H2_TOP_BLUE2
            "BOT": 'rgba(228,0,255, 0.4)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_ROSA
        },
        2: {
            //SS 07_03
            "TOP": 'rgba(255,0,0, 0.4)', // H2 CLOUD 006 //H2_TOP_NEON RED
            "BOT": 'rgba(252,55,231, 0.2)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_PINK1
        },
        1: {
            //SS 07_02
            "TOP": 'rgba(56,101,4, 0.4)', // H2 CLOUD 006 //H2_TOP_MILITARY GREEN
            "BOT": 'rgba(138,255,0, 0.4)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_NEON
        },
        0: {
            //SS 07_01
            "TOP": 'rgba(150,075,250, 0.4)', // H2 CLOUD 006 //H2_TOP_MAGENTA
            "BOT": 'rgba(150,075,250, 0.2)', // ETHANOL CLOUD 001 & 002 // ETHANOL_BOT_MAGENTA2}
        }
    };

    const numMSOpts = 8;
    const numSSOpts = 7;
    const mSetSelector = Math.floor(Math.abs(deltaTemp) % numMSOpts);
    const sSetSelector = Math.floor(Math.abs(breathTemp) % numSSOpts);
    [module.MS_01, module.MS_02, module.MS_03, module.MS_04 , module.MS_05, module.MS_06] = Object.values(colorMainSets[mSetSelector]);
    const newColorSubSets = {
        ...colorSubSets,
        6: {
            "TOP": colorUniSets[mSetSelector].TOP,
            "BOT": colorUniSets[mSetSelector].BOT,
        }
    };
    [module.TOP, module.BOT] = Object.values(newColorSubSets[sSetSelector]);
    module.BLACK = 'rgb(0,0,0)';
    module.WHITE = 'rgba(255,255,255, 0.1)';
    module.WHITE1 = 'rgba(255,255,255, 1)';
    module.WHITE2 = 'rgba(255,255,255, 0.3)';
    module.WHITE3 = 'rgba(255,255,255, 0.5)';
    return module;
};
