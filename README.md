# bacnet-csv-logger

1. **Dual-Script System with Platform-Specific Functions**:
   - **Linux-Based Data Scraping Script**: This script is tailored to run on a Linux system within the building's Operational Technology (OT) LAN. It is specifically designed for connectivity with the Building Automation System (BAS). Its primary function is to continuously scrape data from the BACnet system, leveraging asynchronous operations for flexibility and efficiency. The script can adjust its data scraping rate (throttling) based on the device configurations within the BAS.
   - **Windows-Based Data Retrieval Script**: In contrast, a separate script is crafted to operate on a remote Windows machine. This script is integrated into the organization's SharePoint system for project data synchronization. Its main purpose is to handle the secure retrieval of data from the Linux machine.

2. **Asynchronous and Throttled Data Collection on Linux**:
   - The Linux script continuously collects data from the BACnet system in an asynchronous manner. This approach ensures minimal impact on system resources and allows for adaptable performance based on the BAS's current load and device settings.
   - Data is systematically archived into daily CSV files, ensuring organized and timely storage of information.

3. **Daily Data Transfer via Windows Script**:
   - The Windows script is programmed to run once a day. Its primary task is to securely connect to the Linux machine and retrieve the archived CSV files.
   - The transfer of data is facilitated using SCP (Secure Copy Protocol) over a VPN, ensuring a high level of security during the data transmission process.
   - Post-transfer, the data is synchronized with the organization’s SharePoint system, facilitating centralized and secure storage of the building's automation data.

4. **Efficient and Secure Workflow**:
   - This dual-script setup enables an efficient workflow where continuous, real-time data collection is handled by the Linux system, and secure, daily data transfer and synchronization are managed by the Windows system.
   - The division of tasks between two scripts, optimized for their respective operating systems, ensures robust performance and enhances the overall security and reliability of the data handling process.