from unittest.mock import patch

import pytest

from pickpockett.magnet import get_magnet


@pytest.mark.parametrize(
    ["display_name", "expected"],
    [
        (None, "magnet:?xt=urn:btih:647aa53c56d7277eeb00c0c6d26e663181158cac"),
        (
            "Solar Opposites",
            "magnet:?xt=urn:btih:647aa53c56d7277eeb00c0c6d26e663181158cac&dn=Solar+Opposites",
        ),
    ],
)
def test_get_magnet(display_name, expected):
    html = """
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
        <html lang="uk" dir="ltr">
        <body bgcolor="#E5E5E5" text="#000000" link="#006699" vlink="#5493B4">
        <table width="95%" border="0" cellpadding="2" cellspacing="1" class="btTbl" align="center">
            <tr class="row4_to">
                <td width="165" class="gensmall" rowspan="6" align="center" style="padding: 5px"><img src="images/icon_download.gif" alt="" border="0" />&nbsp;&nbsp;<a title="Завантажити через magnet (без ведення статистики на сайті)" href="magnet:?xt=urn:btih:647aa53c56d7277eeb00c0c6d26e663181158cac"><img style="vertical-align: 50%" src="images/magnet2.gif" alt="" border="0" /></a><br /><h3><strong><a title="Завантажити торрент" rel="nofollow" class="piwik_download"href="download.php?id=673294">Завантажити</a></strong></h3> <br/><br/></td>
            </tr>
        </table>
        </body>
        </html>
    """
    with patch("pickpockett.page._get_page", return_value=(html, "", "")):
        magnet, _ = get_magnet("", "", "", display_name)
        assert magnet.url == expected
