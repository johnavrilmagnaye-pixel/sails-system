# Third-party frontend licenses and notices

This file covers the frontend assets distributed from `static/` and
`apps/*/static/`.

The project license in `LICENSE` does not replace the licenses below. Common
license texts are retained in `LICENSES/`; copyright banners in vendored source
files must also be preserved.

## Components

| Component | Exact upstream ref | License | Copyright / attribution | Decision |
| --- | --- | --- | --- | --- |
| Chart.js 2.9.4 | [v2.9.4](https://github.com/chartjs/Chart.js/tree/v2.9.4) | MIT | Copyright 2020 Chart.js contributors | pinned; final 2.x |
| SortableJS 1.15.6 | [1.15.6](https://github.com/SortableJS/Sortable/tree/1.15.6) | MIT | RubaXa and contributors | pinned; sole sorting library |
| Bootbox 4.4.0 | [v4.4.0](https://github.com/makeusabrew/bootbox/tree/v4.4.0) | MIT | Copyright Nick Payne | pinned; final 4.x |
| Bootstrap 3.4.1 | [v3.4.1](https://github.com/twbs/bootstrap/tree/v3.4.1) | MIT | Copyright 2011-2019 Twitter, Inc.; normalize.css contributors | pinned; final 3.x |
| bootstrap-daterangepicker 2.1.27 | [v2.1.27](https://github.com/dangrossman/daterangepicker/tree/v2.1.27) | MIT | Copyright 2012-2017 Dan Grossman | pinned; final 2.x |
| Font Awesome 4.7.0 | [v4.7.0](https://github.com/FortAwesome/Font-Awesome/tree/v4.7.0) | CSS: MIT; fonts: OFL-1.1 | Font Awesome by Dave Gandy | keep notices |
| FullCalendar Standard 2.9.1 | [v2.9.1](https://github.com/fullcalendar/fullcalendar/tree/v2.9.1) | MIT | Copyright 2016 Adam Shaw | pinned; final 2.x, no premium code |
| Ionicons 2.0.0 | [v2.0.0](https://github.com/ionic-team/ionicons/tree/v2.0.0) | MIT; some Material-derived glyphs CC BY 4.0 | Ben Sperry/Ionic; Material Design Icons by Google | replace, retain attribution until removed |
| blueimp jQuery File Upload 5.42.1 | [5.42.1](https://github.com/blueimp/jQuery-File-Upload/tree/5.42.1) | MIT | Copyright 2010 Sebastian Tschan | replace |
| jQuery UI Widget 1.11.1 | [1.11.1](https://github.com/jquery/jquery-ui/tree/1.11.1) | MIT | Copyright 2014 jQuery Foundation and contributors | replace with upload plugin |
| jQuery Highlight | [45129df2](https://github.com/knownasilya/jquery-highlight/tree/45129df2a641468dbc3e3a800b7d0b6211776d85) | MIT | Copyright 2009 Bartek Szopka; based on Johann Burkard highlight v3 | replace small helper |
| jQuery Masked Input 1.4.1 | [1.4.1](https://github.com/digitalBush/jquery.maskedinput/tree/1.4.1) | MIT | Copyright 2007-2015 Josh Bush | replace small adapter |
| jQuery 1.12.4 | [1.12.4](https://github.com/jquery/jquery/tree/1.12.4) | MIT | jQuery Foundation and contributors; includes Sizzle.js | pinned; final 1.x, EOL risk recorded |
| Lodash custom 3.10.1 | [3.10.1](https://github.com/lodash/lodash/tree/3.10.1) | MIT | Dojo Foundation, Jeremy Ashkenas and contributors | pinned; final 3.x |
| Moment.js 2.30.1 | [2.30.1](https://github.com/moment/moment/tree/2.30.1) | MIT | Tim Wood, Iskren Chernev and contributors | pinned; maintenance mode |
| Select2 Bootstrap Theme 0.1.0-beta.10 | [0.1.0-beta.10](https://github.com/select2/select2-bootstrap-theme/tree/0.1.0-beta.10) | MIT | Select2 Bootstrap Theme contributors | pinned with Select2 4.0.x |
| Select2 4.0.13 | [4.0.13](https://github.com/select2/select2/tree/4.0.13) | MIT | Select2 contributors | pinned; final stable 4.0.x |
| smalot bootstrap-datetimepicker 2.3.4 | [2.3.4](https://github.com/smalot/bootstrap-datetimepicker/tree/2.3.4) | Apache-2.0 | Stefan Petre, Andrew Rowls, Sébastien Malot, Yun Lai, Kenneth Henderick | replace local fork |
| urlize.js | [9ec437e7](https://github.com/ljosa/urlize.js/tree/9ec437e75a3bf1b55d88798109a540c3f421707c) | MIT | Vebjorn Ljosa; Cross-Browser Split copyright 2007-2012 Steven Levithan | replace local fork |
| Vue.js 1.0.28 | [v1.0.28](https://github.com/vuejs/vue/tree/v1.0.28) | MIT | Copyright 2013-2016 Evan You | keep pinned |
| Vue Router 0.7.13 | [v0.7.13](https://github.com/vuejs/vue-router/tree/v0.7.13) | MIT | Copyright 2013-2016 Evan You | keep pinned |
| X-editable 1.5.1 | [v1.5.1](https://github.com/vitalets/x-editable/tree/v1.5.1) | MIT | Copyright 2013 Vitaliy Potapov | replace local fork |

The old Vue.Draggable build, local `vuedraggablefor.js` adapter,
jquery-sortable, Chart.js 1.x, Magnific Popup, html5shiv, and Respond.js were
removed in stage 2. Table sorting now uses the same pinned SortableJS runtime
as the other drag-and-drop behavior.

## Legacy runtime npm graph

`static/legacy-runtime/package.json` contains exact versions and a source-file
to vendored-file mapping for the Vue 1 CRM runtime. Its lock file pins npm
tarball origins and integrity hashes.

## Recorded local modifications

These files must not be refreshed from a CDN or upstream archive without first
porting and testing the recorded behavior:

- `static/patches/bootstrap-datetimepicker.js`: upstream smalot 2.3.4 plus a
  four-line horizontal-position adjustment when the widget is inside
  `.filters`.
- `static/patches/bootstrap-editable.js`: upstream X-editable 1.5.1 plus Select2
  multiple-value option population, a guarded `destroy`, and a `<select
  multiple>` template (18 changed lines against the pristine vendored file).
- `static/libs/urlize/urlize.js`: upstream commit `9ec437e7` plus two semantic
  changes: the `ru`, `ua`, `kz`, and `by` TLDs and forced `target="_blank"`.
- Widget translations are generated from gettext at runtime. The previously
  vendored Moment, FullCalendar, Select2, and datetimepicker locale bundles
  were removed during modernization stage 4.

When upgrading a fork, regenerate a clean upstream file and
apply the behavior in an explicit adapter or a reviewable patch; never edit a
new vendored copy silently.

## FullCalendar product boundary

The distributed files are FullCalendar Standard 2.9.1 (`fullcalendar.js`, core
styles, and the `ru` locale). There are no Scheduler, resource
timeline, resource time-grid, premium common, or premium print optimization
files. FullCalendar Standard 2.9.1 is retained under MIT; this notice does not
authorize adding a premium plugin.

## License texts

- MIT: [LICENSES/MIT.txt](LICENSES/MIT.txt)
- BSD 3-Clause: [LICENSES/BSD-3-Clause.txt](LICENSES/BSD-3-Clause.txt)
- Apache 2.0: [LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt)
- SIL Open Font License 1.1: [LICENSES/OFL-1.1.txt](LICENSES/OFL-1.1.txt)
- Creative Commons Attribution 4.0: [LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt)

MIT notices embedded in a source file remain part of that source. The common
MIT text above is distributed together with the per-component copyright lines
in this document.
