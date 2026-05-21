---
title: "Catalog SOP: Error 90118"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-90118"
captured_at: "2026-05-12T07:07:49Z"
---

# Catalog SOP: Error 90118

Source: https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-90118

## **Error 90118**

**Who is this for?**All individuals who are encountering Error 90118.

**Objective**: To provide SKU within the allowed number of bytes and enable the successful upload of the flat file.

**Instructions:**

This error occurs when the entered value for SKU exceeds the maximum number of bytes (characters) allowed: 40

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/error-90118-image-903pbd7l.png?sv=2022-11-02&spr=https&st=2025-01-29T17%3A54%3A05Z&se=2025-01-29T18%3A04%3A05Z&sr=c&sp=r&sig=tUpFoejYucIuB1FRwQFZVkUvQnwoNNOD0Y8HR3llE9g%3D)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fXkimage.png)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.54.54%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JXmimage.png)

Sample, the screenshots above show that the parent SKU exceeds the 40 characters limit. To fix this, shorten the SKU with the allowed characters and resubmit the feed file with the new SKU.

**Note**: Amazon counts the space with regard to the bytes (characters) limit. Use [https://charcounter.com/en/](https://charcounter.com/en/) to verify the character count.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.55.02%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/RdVimage.png)

FAQs

**1. What does Error 90118 mean, and why am I encountering it?**

- Error 90118 occurs when the SKU (Stock Keeping Unit) exceeds the allowed character limit of 40 bytes. This means that the SKU you’ve entered contains too many characters (including spaces and special characters), making it invalid for Amazon’s system. You will need to shorten the SKU to meet the 40-byte limit.

**2. What exactly is a “byte,” and how does it differ from a “character”?**

- A byte refers to a unit of digital information storage, and for this purpose, it counts the total number of characters used in the SKU, including spaces and punctuation marks. Characters are typically letters and numbers, but when special characters like spaces, dashes, or underscores are used, they may take up more than one byte. Amazon counts the total number of bytes (characters and spaces) in the SKU, and this total must not exceed 40 bytes.

**3. How can I check if my SKU exceeds the 40-byte limit?**

- To check the number of bytes in your SKU, you can use online tools like [charcounter.com](http://charcounter.com) to verify your SKU’s character count. Simply enter your SKU into the tool, and it will show you how many bytes it contains. Alternatively, you can count the characters manually, remembering to include spaces and special characters in your count.

**4. How do I shorten my SKU to fit the 40-byte limit?**

- To fix this error, you need to shorten your SKU by reducing the number of characters while keeping it meaningful and easily identifiable. For example, if your SKU is too long, try using abbreviations or removing unnecessary words. Ensure that the new SKU still follows your internal inventory tracking rules and is recognizable. Once you’ve shortened the SKU, resubmit the file with the new SKU.

**5. Can I use special characters (like underscores or dashes) in my SKU?**

- Yes, you can use special characters like hyphens, underscores, or periods in your SKU. However, keep in mind that some special characters might take up more than one byte in the character count. When shortening your SKU, be careful not to overuse special characters, as they could push the SKU over the 40-byte limit.

**6. What should I do if shortening the SKU doesn’t resolve Error 90118?**

- If shortening the SKU doesn’t resolve the error, it could mean that other SKUs in your file also exceed the 40-byte limit. Go through your entire inventory file to check the character count for each SKU. Use a character count tool (like [charcounter.com](http://charcounter.com)) to help identify any other SKUs that need adjustment. Once all the SKUs are within the 40-byte limit, try re-uploading the file again.

**7. How do I know if the fix I made has worked after resubmitting the feed file?**

- After resubmitting the file with the shortened SKU, go back to the Feed Processing Summary tab in Seller Central to check if the error has been resolved. If the error persists, you may need to review the file again or check for other SKUs that exceed the 40-byte limit.

**8. Are there any common mistakes to avoid when shortening SKUs?**

- Yes, be careful not to accidentally remove essential identifying information when shortening your SKU. If you are using abbreviations, make sure they are still meaningful and recognizable. Avoid removing critical product details that could lead to confusion or misidentification of the product in your system. Additionally, ensure that the SKU remains unique and does not duplicate other SKUs.

**9. What should I do if I have multiple SKUs in one file that exceed the 40-byte limit?**

- If you have multiple SKUs in the same file that exceed the 40-byte limit, you will need to shorten each one individually. You can use [charcounter.com](http://charcounter.com) or a similar tool to help you identify the exact byte count for each SKU and then adjust them as needed. It may be helpful to go through your entire inventory file to ensure all SKUs comply with the 40-byte limit.

**10. Can I use a different character count tool if I have trouble with**[**charcounter.com**](http://charcounter.com)**?**

- Yes, there are other character count tools available online that can help you check the byte count of your SKU. Some popular alternatives include WordCounter and Character Count Online. Just make sure the tool you use counts both characters and spaces, as Amazon includes all characters (including spaces and special symbols) in the byte count.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/error-90118-image-903pbd7l.png?sv=2022-11-02&spr=https&st=2025-01-29T17%3A54%3A05Z&se=2025-01-29T18%3A04%3A05Z&sr=c&sp=r&sig=tUpFoejYucIuB1FRwQFZVkUvQnwoNNOD0Y8HR3llE9g%3D
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fXkimage.png
- 3. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.54.54%E2%80%AFAM.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JXmimage.png
- 5. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.55.02%E2%80%AFAM.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/RdVimage.png
