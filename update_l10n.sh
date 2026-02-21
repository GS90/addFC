#!/bin/bash

# translation file updates:
rm ./addon/localization/ui.ts ./addon/localization/code.ts
lupdate ./addon/addFC -ts ./addon/localization/ui.ts
pylupdate5 ./addon/addFC/*.py -ts ./addon/localization/code.ts

# translation file updates, russian:
lupdate ./addon/addFC -ts ./addon/localization/ui_ru.ts
pylupdate5 ./addon/addFC/*.py -ts ./addon/localization/code_ru.ts

exit 0
