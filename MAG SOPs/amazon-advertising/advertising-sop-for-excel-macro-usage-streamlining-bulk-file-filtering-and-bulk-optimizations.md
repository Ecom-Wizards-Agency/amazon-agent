---
title: "Advertising SOP for Excel Macro Usage: Streamlining Bulk File Filtering and Bulk Optimizations"
category: "Amazon Advertising"
source_url: "https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-for-excel-macro-usage-streamlining-bulk-file-filtering-and-bulk-optimizations"
captured_at: "2026-05-12T07:07:49Z"
---

# Advertising SOP for Excel Macro Usage: Streamlining Bulk File Filtering and Bulk Optimizations

Source: https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-for-excel-macro-usage-streamlining-bulk-file-filtering-and-bulk-optimizations

## **Advertising SOP for Excel Macro Usage:**

**Streamlining Bulk File Filtering and Bulk Optimizations**

**Who is this for?**

This SOP is intended for anyone managing advertising campaigns.

**Objective:**

The objective of this SOP is to guide users through a series of steps to enhance their Amazon advertising workflow. Specifically, it aims to automate the process of filtering, sorting, and adding new columns to a bulk file containing data related to Sponsored Products (SP), Sponsored Brands (SB), and Sponsored Display (SD) campaigns. The provided macros facilitate these tasks, ensuring efficiency and accuracy in campaign management.

**Video demo from one of MAG's PPC Specialists:**

[Macro Code](https://docs.google.com/document/d/1-xzFgh2g583s-hbMnt2wSj6mtTPTO9cRCjlY6BMQ-70/edit?usp=sharing)

**Note: Your bulk file should include SB and SD data or else our Macro will not work.**

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/LzAimage.png)

**Procedure:**

1. Enabling the Developer Option in Excel

- Open Excel.
- Navigate to 'Options' > 'Customize Ribbon' > 'Main Tabs'.
- Check the box beside 'Developer'.
- Click 'OK'.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-FFT86QN8.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/4SPimage.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/uQcimage.png)

2. Recording a Dummy Macro

- Open the bulk file and enable editing.
- Go to the 'Developer' tab and click 'Record Macro'.
- Store the macro in the 'PERSONAL MACRO WORKBOOK'.
- Type random text in one cell and press 'Stop Recording'.
- This creates a dummy module folder in Excel.

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/OcLimage.png)

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-L7EKP2WC.png)

3. Deleting Dummy Macro Code

- Click the 'VISUAL BASIC' tab.
- Open 'VBA Project (PERSONAL)', then open 'Module 1'.
- Delete the dummy macro code.

  (In this example, it’s in module 2 because I already have a Macro in Module 1.)

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-PIMQ074F.png)

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/cjbimage.png)

4. Inserting Custom Macro Code

OPTION 1: Copy and paste the code below into the module

##### **OPTION 1: Copy and paste the code below into the module**

Sub ForBulk()

Sheets("Sponsored Products Campaigns").Columns("AL:AP").Delete

Sheets("Sponsored Products Campaigns").Columns("AD:AE").Delete

Sheets("Sponsored Products Campaigns").Select

Range("A1").Select

Selection.AutoFilter

Range("A:T").AutoFilter Field:=2, Criteria1:=Array("Campaign"), Operator:=xlFilterValues

Range("A1").Select

Range(Selection, Selection.End(xlToRight)).Select

Range(Selection, Selection.End(xlDown)).Select

Selection.Copy

Sheets.Add After:=ActiveSheet

ActiveSheet.Name = "Campaign"

ActiveSheet.Paste

Sheets("Sponsored Products Campaigns").Select

Range("A1").Select

Selection.AutoFilter

Range("A:T").AutoFilter Field:=2, Criteria1:=Array("Keyword", "Product Targeting"), Operator:=xlFilterValues

Range("A:T").AutoFilter Field:=18, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Range("A:T").AutoFilter Field:=19, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Range("A:T").AutoFilter Field:=20, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Dim LastRow As Long

LastRow = Range("A" & Rows.Count).End(xlUp).Row

Range("A1:AT" & LastRow).Sort _

Key1:=Range("AR1"), Order1:=xlDescending, _

Key2:=Range("AM1"), Order2:=xlDescending, _

Key3:=Range("AJ1"), Order3:=xlDescending, _

Header:=xlYes

Range("AU1").Select

ActiveCell.FormulaR1C1 = "New"

Range("AV1").Select

ActiveCell.FormulaR1C1 = "Min"

Range("AW1").Select

ActiveCell.FormulaR1C1 = "Max"

Range("AX1").Select

ActiveCell.FormulaR1C1 = "Old"

Range("AY1").Select

ActiveCell.FormulaR1C1 = "Strat"

Dim lastRow1 As Long

lastRow1 = Cells(Rows.Count, "A").End(xlUp).Row

Range("AV2:AV" & lastRow1).Formula = "=MIN(AS2,AX2)"

Range("AW2:AW" & lastRow1).Formula = "=MAX(AS2,AX2)"

Range("AX2:AX" & lastRow1).Formula = "=IF(AB2="""",AA2,AB2)"

Range("AY2:AY" & lastRow1).Formula = "=INDEX(Campaign!AE:AE,MATCH(L2,Campaign!L:L,0))"

'SB

Sheets("Sponsored Brands Campaigns").Columns("AJ").Delete

Sheets("Sponsored Brands Campaigns").Select

If (Range("A2") = "") Then GoTo SD

Range("A1").Select

Selection.AutoFilter

Range("A:X").AutoFilter Field:=2, Criteria1:=Array("Keyword", "Product Targeting"), Operator:=xlFilterValues

Range("A:X").AutoFilter Field:=15, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Range("A:X").AutoFilter Field:=16, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Range("A:X").AutoFilter Field:=17, Criteria1:="=Out Of Budget", Operator:=xlOr, Criteria2:="=Running"

Dim SBlastRow As Long

SBlastRow = Range("A" & Rows.Count).End(xlUp).Row

Range("A1:AX" & SBlastRow).Sort _

Key1:=Range("AV1"), Order1:=xlDescending, _

Key2:=Range("AQ1"), Order2:=xlDescending, _

Key3:=Range("AN1"), Order3:=xlDescending, _

Header:=xlYes

Range("AY1").Select

ActiveCell.FormulaR1C1 = "New"

Range("AZ1").Select

ActiveCell.FormulaR1C1 = "Min"

Range("BA1").Select

ActiveCell.FormulaR1C1 = "Max"

Range("BB1").Select

ActiveCell.FormulaR1C1 = "Old"

Dim SBlastRow1 As Long

SBlastRow1 = Cells(Rows.Count, "A").End(xlUp).Row

Range("AZ2:AZ" & SBlastRow1).Formula = "=MIN(AW2,BB2)"

Range("BA2:BA" & SBlastRow1).Formula = "=MAX(AW2,BB2)"

Range("BB2:BB" & SBlastRow1).Formula = "=V2"

Selection.AutoFilter

ActiveSheet.Range("A:BB").AutoFilter Field:=52, Criteria1:="<>"

SD:

Sheets("Sponsored Display Campaigns").Columns("AP:AU").Delete

Sheets("Sponsored Display Campaigns").Select

Range("A1").Select

Selection.AutoFilter

Range("A:AO").AutoFilter Field:=2, Criteria1:=Array("Audience Targeting", "Contextual Targeting"), Operator:=xlFilterValues

Range("A:AO").AutoFilter Field:=16, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Range("A:AO").AutoFilter Field:=17, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Range("A:AO").AutoFilter Field:=18, Criteria1:=Array("Enabled"), Operator:=xlFilterValues

Dim SDlastRow As Long

SDlastRow = Range("A" & Rows.Count).End(xlUp).Row

Range("A1:AO" & SDlastRow).Sort _

Key1:=Range("AM1"), Order1:=xlDescending, _

Key2:=Range("AH1"), Order2:=xlDescending, _

Key3:=Range("AE1"), Order3:=xlDescending, _

Header:=xlYes

Range("AP1").Select

ActiveCell.FormulaR1C1 = "New"

Range("AQ1").Select

ActiveCell.FormulaR1C1 = "Min"

Range("AR1").Select

ActiveCell.FormulaR1C1 = "Old"

Dim SDlastRow1 As Long

SDlastRow1 = Cells(Rows.Count, "A").End(xlUp).Row

Range("AQ2:AQ" & SDlastRow1).Formula = "=Min(AN2,AR2)"

Range("AR2:AR" & SDlastRow1).Formula = "=IF(Z2="""",Y2,Z2)"

Selection.AutoFilter

ActiveSheet.Range("A:AQ").AutoFilter Field:=43, Criteria1:="<>"

'Last steps

Worksheets("Campaign").Visible = False

Sheets("Sponsored Products Campaigns").Select

Selection.AutoFilter

ActiveSheet.Range("A:AY").AutoFilter Field:=48, Criteria1:="<>"

Range("AU1").Select

End Sub

Sub BulkToNewWB()

Dim NewWorkbook As Workbook

Dim SourceWorkbook As Workbook

Dim SPData As Worksheet

Dim SBData As Worksheet

Dim SDData As Worksheet

Dim TargetSheet As Worksheet

Dim LastRow As Long

Dim ws As Worksheet

Dim SourceWorkbookName As String

Dim WorkbookFound As Boolean

' Set references to the new workbook

Set NewWorkbook = Workbooks.Add

' Initialize the flag

WorkbookFound = False

' Find and set references to the source workbook that starts with "bulk"

For Each SourceWorkbook In Workbooks

If Left(SourceWorkbook.Name, 4) = "bulk" Then

WorkbookFound = True

Exit For

End If

Next SourceWorkbook

' Check if the source workbook is found and open

If Not WorkbookFound Then

MsgBox "The source workbook is not open.", vbExclamation

Exit Sub

End If

' Set references to the new workbook's sheets

Set SPData = NewWorkbook.Sheets.Add(After:=NewWorkbook.Sheets(NewWorkbook.Sheets.Count))

SPData.Name = "SP"

Set SBData = NewWorkbook.Sheets.Add(After:=NewWorkbook.Sheets(NewWorkbook.Sheets.Count))

SBData.Name = "SB"

Set SDData = NewWorkbook.Sheets.Add(After:=NewWorkbook.Sheets(NewWorkbook.Sheets.Count))

SDData.Name = "SD"

' Copy data from the source workbook's sheets

CopyDataFromSourceSheet SourceWorkbook, "Sponsored Products Campaigns", SPData

CopyDataFromSourceSheet SourceWorkbook, "Sponsored Brands Campaigns", SBData

CopyDataFromSourceSheet SourceWorkbook, "Sponsored Display Campaigns", SDData

' Loop through each sheet and add "update" in column C for rows with data

For Each ws In NewWorkbook.Sheets

LastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row

If LastRow > 1 Then

ws.Range("C2:C" & LastRow).Value = "update"

End If

Next ws

' Delete the default "Sheet1" in the new workbook

Application.DisplayAlerts = False ' Turn off alerts

NewWorkbook.Sheets("Sheet1").Delete

Application.DisplayAlerts = True ' Turn on alerts

End Sub

Sub CopyDataFromSourceSheet(SourceWorkbook As Workbook, SourceSheetName As String, TargetSheet As Worksheet)

Dim LastRow As Long

LastRow = SourceWorkbook.Sheets(SourceSheetName).Cells(SourceWorkbook.Sheets(SourceSheetName).Rows.Count, "A").End(xlUp).Row

SourceWorkbook.Sheets(SourceSheetName).UsedRange.Copy Destination:=TargetSheet.Range("A1")

End Sub

Sub WordCount()

ActiveCell.FormulaR1C1 = "=LEN(TRIM(RC[-1]))-LEN(SUBSTITUTE(RC[-1],"" "",""""))+1"

End Sub

If you can’t copy the macro code from above click [HERE](https://docs.google.com/document/d/1-xzFgh2g583s-hbMnt2wSj6mtTPTO9cRCjlY6BMQ-70/copy)

OPTION 2: Download module

##### **OPTION 2: Download module**

**For Importing MACRO:** Download this module: [**Module1.3.bas**](https://drive.usercontent.google.com/download?id=181UB0wgJnVIoQmCGrqHK9X-bJANloure&export=download&authuser=2)

**Go to Developer > Visual Basic > Right Click VBA Project Personal**

**Remove the old module first**

**Import File > select Module1.bas**

**Press CTRL + S and close Visual Basic**

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JHpimage.png)

5. Saving and Setting Shortcut Keys

- Press 'Ctrl + S' to save and close the Visual Basic UI.
- Open 'MACROS' and set shortcut keys for each macro:

  - For Bulk To New WB: 'Ctrl + Shift + N'
  - For Bulk Filter: 'Ctrl + Shift + Q'
  - For Word Count: 'Ctrl + Shift + W'
- Save and close the bulk file.

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-Q5ZX28MD.png)

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/s1cimage.png)

6. Testing the Macro

- Reopen the bulk file and test the shortcut key 'CTRL + Shift + Q'.
- The macro will filter targets, sort data, and add new columns for bid to CPC computation and bidding strategy.

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-3MWWS3X5.png)

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/rzNimage.png)

7. Preparing Data for New Workbook

- After setting new bids, filter the 'New Bid' column to remove blanks.
- Use the macro 'CTRL + SHIFT + N' to transfer filtered data to a new workbook.

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/04Simage.png)

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-KAARWRM1.png)

  This will transfer the filtered data from bulk to a new workbook and automatically add “update” to the operations column.

  *Note:* If there’s a blank workbook, please delete it before uploading your bulk.

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-AFHBES7F.png)

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ITkimage.png)

  > Before uploading your bulk file make sure to check the following
  >
  > - **Before Copy-Pasting Data:**
  >
  >   - Ensure no filters are selected when copying into a sheet with formulas.
  >   - Remove any data where bids were not change before copying.
  >   - Always use Copy → Paste → Values to prevent formula errors.
  > - **Formatting & Accuracy:**
  >
  >   - Check decimal place formatting to avoid converting cents into whole dollars.
  >   - Verify daily budget decimal formatting in the campaign column.
  >   - Double-check margins on new bids (especially if using drag-to-copy).
  > - **Data Validation:**
  >
  >   - Compare the new sheet vs. the old sheet to ensure bid changes were applied correctly.
  >   - Verify that each keyword correctly corresponds to its intended bid before uploading.
  >   - Ensure that no keywords are mismatched with incorrect bids.
  >   - Ensure columns R, S, and T are filtered to "Enabled".
  > - **Final Upload Process:**
  >
  >   - Upload every bulk file to the Asana task before marking it complete.
  >   - For large bulk files, upload to the client’s folder and paste the link in the Asana task comments.

8. Final Steps

- In the new workbook, copy and paste the new bid into the 'BID' column. Delete any blank workbook before uploading your bulk.
- Save the file. It is now ready for upload.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-EQ6GUSRI.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/tloimage.png)

*NOTE:*

- Ensure that your bulk file incorporates SB and SD data; otherwise, our Macro will not function correctly.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/hSWimage.png)

- Ensure the bulk file is not renamed from its default name for the code to apply correctly.
- Delete any blank workbook before uploading your bulk.

FAQs

##### **FAQs**

Prerequisites

- **Q1: What should my bulk file include for the macros to work?**

  - **A1:** The bulk file must include data for Sponsored Brands (SB) and Sponsored Display (SD) campaigns; otherwise, the macros will not function.
- **Q2: Why shouldn't I rename my bulk file?**

  - **A2:** Renaming the bulk file from its default name will prevent the macros from applying correctly.

Macro Setup

- **Q3:** How do I enable the Developer option in Excel?

  - **A3:**

    - Open Excel.
    - Go to 'Options' > 'Customize Ribbon' > 'Main Tabs.'
    - Check the box beside 'Developer.'
    - Click 'OK.'
- **Q4:** How do I create a dummy macro to set up the module folder?

  - **A4:**

    - Open the bulk file and enable editing.
    - Go to the 'Developer' tab and click 'Record Macro.'
    - Store the macro in the 'PERSONAL MACRO WORKBOOK.'
    - Type random text in one cell and press 'Stop Recording.'
- **Q5:** How do I insert custom macro code?

  - **A5:**

    - OPTION 1: Copy and paste the provided macro code into the module via Visual Basic.
    - OPTION 2: Download and import the module file.

Shortcut Keys

- **Q6:** How do I assign shortcut keys for macros?

  - **A6:**

    - Save and close the Visual Basic UI with 'Ctrl + S.'
    - Open the 'MACROS' menu and assign shortcuts:

      - Bulk To New WB: 'Ctrl + Shift + N'
      - Bulk Filter: 'Ctrl + Shift + Q'
      - Word Count: 'Ctrl + Shift + W'

Testing and Usage

- **Q7:** How do I test the macros?

  - **A7:** Reopen the bulk file and use the shortcut key 'Ctrl + Shift + Q.' The macro will filter, sort data, and add new columns for bid calculations and strategy.
- **Q8:** How do I prepare data for a new workbook?

  - **A8:** After setting new bids, filter the 'New Bid' column to remove blanks. Use the macro shortcut 'Ctrl + Shift + N' to transfer filtered data to a new workbook.

Final Steps

- **Q9:** What are the final steps before uploading the bulk file?

  - **A9:**

    - Copy and paste the new bid into the 'BID' column in the new workbook.
    - Delete any blank workbook.
    - Save the file.
- **Q10:** What should I check before uploading the bulk file?

  - **A10:** Ensure the bulk file includes SB and SD data, hasn't been renamed, and that any blank workbook is deleted.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/LzAimage.png
- 2. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-FFT86QN8.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/4SPimage.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/uQcimage.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/OcLimage.png
- 6. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-L7EKP2WC.png
- 7. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-PIMQ074F.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/cjbimage.png
- 9. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JHpimage.png
- 10. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-Q5ZX28MD.png
- 11. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/s1cimage.png
- 12. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-3MWWS3X5.png
- 13. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/rzNimage.png
- 14. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/04Simage.png
- 15. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-KAARWRM1.png
- 16. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-AFHBES7F.png
- 17. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ITkimage.png
- 18. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-EQ6GUSRI.png
- 19. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/tloimage.png
- 20. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/hSWimage.png
