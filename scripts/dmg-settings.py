# SPDX-License-Identifier: AGPL-3.0-only
# Build with dmgbuild -D app=... -D docs=... -D background=... -s this_file Volume output.dmg
files=[defines['app'],(defines['docs'],'Documentatie')]
symlinks={'Applications':'/Applications'}
background=defines['background']
format='UDZO'
filesystem='HFS+'
window_rect=((160,140),(760,600))
default_view='icon-view'
show_status_bar=False
show_tab_view=False
show_toolbar=False
show_pathbar=False
show_sidebar=False
icon_size=80
text_size=12
icon_locations={'Tickertwister Desktop.app':(185,235),'Applications':(575,235),'Documentatie':(630,420)}
include_icon_view_settings=True
include_list_view_settings=False
