@echo off
REM Batch file to fix Hebrew display in CMD
REM Run this before running Python scripts

chcp 65001 >nul
echo Hebrew display fix applied!
echo Test: אלינור בדיקה
echo.
echo If Hebrew displays correctly above, the fix worked!
echo This fix applies to this terminal session only.
echo.

