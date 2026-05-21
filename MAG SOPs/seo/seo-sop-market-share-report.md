---
title: "SEO SOP: Market Share Report"
category: "SEO"
source_url: "https://sop.myamazonguy.com/books/seo/page/seo-sop-market-share-report"
captured_at: "2026-05-12T07:07:49Z"
---

# SEO SOP: Market Share Report

Source: https://sop.myamazonguy.com/books/seo/page/seo-sop-market-share-report

## **Market Share Report**

**Who is this for :** For those who wish to extract and organize search query performance data and use them for Advertising and SEO purposes.

**Objectives:**

- Provide visibility into the performance of the top search terms associated with your brand, based on customer search behavior.
- Fine-tune marketing strategies and enhance listings by adding keywords that align with customer interests.
- Provide an opportunity for development in the Advertising or SEO departments.

Manual Template

### **Manual Template**

**Sample worksheet:** [Age of Sage - Market Share Report](https://docs.google.com/spreadsheets/d/1OrVXynkeUiCerilU4HxeLMRUgo5MnzNpLIGZMSrwI4k/copy)

**I. Extract Data from Search Query Performance**

1. Go to Brands then Brand Analytics from the menu.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/m26image.png)

1. From there, click on Search Analytics then Search Query Performance, which is located at the top-center of the page.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-09-18%20at%202.55.08%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fbJimage.png)

1. Select the account, reporting range, year, as well as month from which you are pulling the data. For this training purpose, we shall be choosing monthly as the reporting range and 2024 as the target year.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-09-18%20at%203.02.13%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/6JQimage.png)

1. Then, download the report, access the report, and paste all data into your worksheet. Use the current month and year as the title. For example, January 2024.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-09-18%20at%202.57.17%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FBCimage.png)

When downloading data from the first month, download up to 100 search queries only. You can download up to 500 search queries for the succeeding months. This is because we want to compare the first month's data with the most recent data to determine any major differences.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/A3(1).png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/m4Eimage.png)

**II. Search Query Organization**

Using the [template](https://docs.google.com/spreadsheets/d/1eoS37E2FmQ4GnJihH7XfukmPxbS0QtNgmotKeoegyGQ/copy), on the raw monthly data tab, arrange the search queries using the search query score from A to Z. Then, copy all the figures in the following columns and paste them onto the Summary sheet:

- Search Query
- Rank
- Search Query Volume
- Impressions - Brand Share (column F)
- Clicks - Brand Share (column J)
- Cart Adds - Brand Share (column S)
- Purchases - Brand Share (column AB)

The values in columns I-M will be calculated automatically since the formulas are already included. Be sure to do this for all the succeeding months.

Furthermore, complete Search Query (column A) and the first rank data (column C) from the first month in the four brand share individual tabs. They must remain the same throughout the months/years, as they are static. Then, complete the data for the first month.

To continuously update the worksheet with the most recent month, apply the following formulas below:

- [Current Rank]

=IFERROR(VLOOKUP(firstsearchquery,'currentmonth'!A:B,2,false),"-")

- [Brand Share % Increment]

=IFERROR(currentbrandshare-firstbrandshare,"-")

- [Search Query Volume] - for Impressions

=IFERROR(VLOOKUP(firstsearchquery,'currentmonth'!A:C,3,false),"-")

- [Total Count] - for Impressions

=IFERROR(VLOOKUP(firstsearchquery,'currentmonth'!A:D,4,FALSE),"-")

- [Brand Count] - for Impressions

=IFERROR(VLOOKUP(firstsearchquery,'currentmonth'!A:E,5,FALSE),"-")

- [Brand Share] - for Impressions

=iferror(vlookup(firstsearchquery,'currentmonth'!A:F,6,false),"-")

The formulas above are used to check the data in the current month column of a range and return the corresponding value from a target column if it exists. If there is an error, it will return a dash (-) instead.

Repeat the same process for the other data on**Brand Share - Clicks, Cart Adds**, and **Purchases** with the needed adjustments on the formulas. For example, on the**Brand Share - Clicks**tab, copy the same formulas applied in the **Brand Share - Impressions** tab, however, adjust the range from A:G and the target value from 4 to 7.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/A4.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/3Tlimage.png)

**Pro tip:** For every Brand Share tab, use the following codes to guide you with the range and target values. Verify the placement of data at every start of the week to ensure the codes are still appropriate.

- 4 5 6 – D E F (Impressions)
- 7 9 10 – G I J (Clicks)
- 16 18 19 – P R S (Cart Adds)
- 25 27 28 – Y AA AB (Purchases)

Next, on the **Summary** sheet, select the top search query with a significant average brand share difference. You can compare the most recent month vs. the previous month, or any from the previous months.

As a result of this training, you should be able to provide visibility into the performance of the top search terms associated with your brand, as well as provide an opportunity for development in other areas, such as Advertising or SEO.

Automated Template with Google Apps

### **Automated Template with Google Apps**

**Scopes:**

- Seller Central accounts with access to Brand Analytics.
- This can be done to all accounts including new ones

**Procedures:**

1. Make a copy of the template and save it to the client folder with the title format - ***Client Name - Market Share Report***

  - **Template:** [Market Share Report - Original V2 Final](https://docs.google.com/spreadsheets/d/1mxJNF2TejLkaBzP6D9CGOgZl3Q6_rHY3zs728cygHwE/copy)

1. Run Data from Search Query Performance

  - Head over to *Brands*and click on *Brand Analytics*.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/TLtimage.png)

- From here, go to *Search Analytics* then*Search Query Performance*.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Didimage.png)

*Figure 2.*

- Select the brand, reporting range: Monthly, year: present year, as well as the month from which you are pulling the data. Hit apply.
- Next, click on the “Generate Download” button, then choose the “Simple View” option and click “Generate Download” once more.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/1TYimage.png)

*Figure 3.*

- **NOTE:**For new accounts, pull the current and the previous month Search Query Performance data.

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/6sKimage.png)

*Figure 4.*

1. Uploading Search Query Performance files to the worksheet

  - From the worksheet, click “*CLICK HERE TO START WORKING*” and select the *upload the SQP files* (figure 5)

    ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/3hOimage.png)

*Figure 5.*

- For new worksheet, a prompt with pop up - “Authorization required” and click “OK”. Choose the account you have used and click “Allow”. Wait for the authorization to be successful. See *Figures 6 and 7*.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ZJfimage.png)

*Figure 6.*

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/SEO-SOP-Market-Share-Report-New-Template-6.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/qC6image.png)

*Figure 7.*

- Once successful, you can now access the files.
- Access the Search Query Performance data from your computer files. Enter the year and the month of the data you are importing. *Ex. 2024-Jan* as shown in Figure 8.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/f17image.png)

*Figure 8.*

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-AA688UQI.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/n50image.png)

*Figure 9.*

- Wait until the sheet finishes its calculations (figure 9). Then, proceed to upload the remaining files and patiently wait for the sheet to complete calculations after each upload.
- Once done uploading, click “*CLICK HERE TO START WORKING*” and then choose “*I am done uploading the files*”.

1. Updating the Brand Share tabs

  - Make use of the Brand Share tabs. Choose the relevant month, and if necessary, include additional columns. Simply copy the previous month's column to acquire the formulas.
  - Do it for Brand Share - Purchases, Add to Cart, Clicks, and Impressions.

1. Data Analysis.

  - Check the data in the Summary and Brand Share tabs. Data should be populated.
  - Utilize features like comparison ranges as needed.
  - If you want to monitor specific keywords, input them into the “Monitored KW” tab starting from cell A6.

By following this SOP, we aim to utilize the Brand Analytics tools within Seller Central to enhance our brand's performance, marketing strategies, and collaboration across departments, leading to improved business outcomes.

FAQs

Data Extraction and Organization

- **Q1: How can I ensure I'm selecting the correct reporting range, year, and month when extracting data?**

  - **A1:** Always choose the "Monthly" reporting range for consistent analysis. For training purposes, select the current year (e.g., 2024) and specify the month you need. Ensure accuracy when selecting the account and brand details to avoid data discrepancies.
- **Q2: Why is only 100 search queries downloaded for the first month?**

  - **A2:** The initial month's limit of 100 queries ensures a manageable dataset for comparison against subsequent months. For following months, increase the limit to 500 queries to capture broader trends.
- **Q3: What should I do if the data download contains errors or unexpected results?**

  - **A3:** Double-check the selected account, reporting range, and filters. If the issue persists, ensure the Search Analytics data is up-to-date in Seller Central and re-download the report.

Worksheet Setup and Maintenance

- **Q4: How do I verify that the worksheet formulas are working correctly?**

  - **A4:** Test the formulas with a small dataset to confirm accurate calculations. For instance, manually verify a few rows against the raw data for consistency.
- **Q5: What should I do if the formulas return an error or a dash ("-") unexpectedly?**

  - **A5:** Check the corresponding columns in the "current month" tab for missing or mismatched data. Ensure the search query data aligns with the expected ranges.
- **Q6: How do I adjust the worksheet for new brand share tabs or additional columns?**

  - **A6:** Copy the formulas from the previous month’s columns and paste them into the new columns. Update the ranges and target values as necessary to match the new dataset.

Automated Template Usage

- **Q7: What should I do if the “Authorization Required” prompt appears when using the automated template?**

  - **A7:** Click "OK," select the account associated with the Google Apps script, and click "Allow." Once authorized, reattempt accessing the Search Query Performance files.
- **Q8: Can I use the automated template for accounts without historical data?**

  - **A8:** Yes, for new accounts, pull data for both the current and previous month to establish a baseline for future comparisons.

Data Analysis and Insights

- **Q9: How do I identify significant trends or insights from the Summary tab?**

  - **A9:** Focus on search queries with notable differences in brand share percentages or rank changes over time. Compare data from the most recent month against prior months to spot trends.
- **Q10: What steps should I take if the Summary tab shows unusual or inconsistent data?**

  - **A10:** Verify the accuracy of the raw data and the formulas applied in the worksheet. Ensure all uploaded files were processed correctly and re-check the Summary tab calculations.

Keyword Monitoring

- **Q11: How can I track specific keywords over time?**

  - **A11:** Use the "Monitored KW" tab starting from cell A6. Input keywords of interest, and the worksheet will automatically track their performance based on the uploaded data.
- **Q12: What criteria should I use to decide which keywords to monitor?**

  - **A12:** Focus on high-performing keywords, those with significant changes in brand share, or those aligned with strategic marketing goals.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/m26image.png
- 2. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-09-18%20at%202.55.08%E2%80%AFAM.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fbJimage.png
- 4. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-09-18%20at%203.02.13%E2%80%AFAM.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/6JQimage.png
- 6. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-09-18%20at%202.57.17%E2%80%AFAM.png
- 7. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FBCimage.png
- 8. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/A3(1).png
- 9. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/m4Eimage.png
- 10. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/A4.png
- 11. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/3Tlimage.png
- 12. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/TLtimage.png
- 13. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Didimage.png
- 14. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/1TYimage.png
- 15. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/6sKimage.png
- 16. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/3hOimage.png
- 17. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ZJfimage.png
- 18. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/SEO-SOP-Market-Share-Report-New-Template-6.png
- 19. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/qC6image.png
- 20. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/f17image.png
- 21. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-AA688UQI.png
- 22. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/n50image.png
