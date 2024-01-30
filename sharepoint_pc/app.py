import os
import pandas as pd
import paramiko
from scp import SCPClient

# this Windows OS machine
KEY_PATH = r"C:\Users\bbartling\.ssh\asdf.pub"
LOCAL_PATH = os.getcwd()

# remote Linux machine SSH/SCP details
HOST = "192.168.0.113"
PORT = 22
USERNAME = "user"
REMOTE_PATH = "/home/project/building/data"
PASSWORD = "admin"


def create_ssh_client(host, port, username, key_path, password=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if password:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                key_filename=key_path,
                password=password,
            )
        else:
            client.connect(
                hostname=host, port=port, username=username, key_filename=key_path
            )

        print("SSH login successful!")  # Print the success message
        return client
    except paramiko.AuthenticationException:
        print("SSH login failed. Check your credentials and key file.")
        raise


def list_csv_files(ssh_client, REMOTE_PATH):
    stdin, stdout, stderr = ssh_client.exec_command(f"ls {REMOTE_PATH}/*.csv")
    # Return each line as a string, stripping any whitespace
    return [line.strip() for line in stdout]


def list_local_files(LOCAL_PATH):
    raw_data_path = os.path.join(LOCAL_PATH, "raw_data")

    # Create raw_data directory if it doesn't exist
    os.makedirs(raw_data_path, exist_ok=True)

    return [
        file
        for file in os.listdir(raw_data_path)
        if os.path.isfile(os.path.join(raw_data_path, file))
    ]


def concatenate_csv_files(raw_data_path, processed_file_path):
    # List all CSV files in the raw_data directory
    csv_files = [
        os.path.join(raw_data_path, file)
        for file in os.listdir(raw_data_path)
        if file.endswith(".csv")
    ]

    # Read and concatenate all CSV files into one DataFrame
    df_list = [pd.read_csv(file) for file in csv_files]
    combined_df = pd.concat(df_list, ignore_index=True)

    # Save the combined DataFrame to a single CSV file
    combined_df.to_csv(processed_file_path, index=False)
    print(f"Combined data saved to {processed_file_path}")


def scp_files(ssh_client, remote_files, LOCAL_PATH):
    # Create raw_data directory if it doesn't exist
    os.makedirs(os.path.join(LOCAL_PATH, "raw_data"), exist_ok=True)

    with SCPClient(ssh_client.get_transport()) as scp:  # Corrected here
        for file in remote_files:
            # Change the local file path to save in raw_data directory
            local_file_path = os.path.join(
                LOCAL_PATH, "raw_data", os.path.basename(file)
            )
            scp.get(file, local_file_path)


def process_csv(file_path):
    # Read the CSV data, skipping any duplicated header row
    df = pd.read_csv(file_path, skiprows=lambda x: x == 1)

    # Convert 'Time' to datetime, coercing errors to NaT
    df["Time"] = pd.to_datetime(
        df["Time"], errors="coerce", format="%Y-%m-%dT%H:%M:%S.%f"
    )

    # Keep only rows where 'Time' is not NaT
    df = df[df["Time"].notna()]

    # Check for duplicates and handle them if necessary
    df = df.drop_duplicates(subset=["Time", "Point Name"], keep="first")

    # Pivot the table to get unique columns for each point name
    pivoted_df = df.pivot(index="Time", columns="Point Name", values="Value")

    # Forward fill and then backfill the gaps
    pivoted_df = pivoted_df.ffill().bfill()

    # Create processed_data directory if it doesn't exist
    processed_directory = "processed_data"
    os.makedirs(processed_directory, exist_ok=True)

    # Save to a new CSV file in the processed_data subdirectory
    processed_file_name = (
        os.path.splitext(os.path.basename(file_path))[0] + "_processed.csv"
    )
    processed_file_path = os.path.join(processed_directory, processed_file_name)
    pivoted_df.to_csv(processed_file_path)

    print(f"Processed file saved as: {processed_file_path}")
    print(df)


def main():
    # Create SSH client and connect with PASSWORD
    ssh_client = create_ssh_client(HOST, PORT, USERNAME, KEY_PATH, PASSWORD)

    # Ensure raw_data and processed_data directories exist
    raw_data_directory = os.path.join(LOCAL_PATH, "raw_data")
    processed_directory = os.path.join(LOCAL_PATH, "processed_data")
    os.makedirs(raw_data_directory, exist_ok=True)
    os.makedirs(processed_directory, exist_ok=True)

    try:
        local_files = list_local_files(LOCAL_PATH)
        print("local files ", local_files)

        # List CSV files in the remote archived directory
        remote_files = list_csv_files(ssh_client, REMOTE_PATH)
        print("remote_files \n", remote_files)

        # Exclude 'bacnet_data.csv' and compare with 
        # local files to decide which files to transfer
        files_to_transfer = [
            file
            for file in remote_files
            if "bacnet_data.csv" not in file
            and os.path.basename(file) not in local_files
        ]
        print("Files to transfer \n", files_to_transfer)

        # SCP the files
        scp_files(ssh_client, files_to_transfer, LOCAL_PATH)

        # If there are files to transfer, process them
        if files_to_transfer:
            # Process each transferred file
            for file in files_to_transfer:
                local_file_path = os.path.join(
                    raw_data_directory, os.path.basename(file)
                )
                process_csv(local_file_path)

            # Path for the combined processed file
            processed_file_path = os.path.join(
                processed_directory, "combined_processed_data.csv"
            )

            # Concatenate all CSV files in raw_data 
            # and save to processed_data
            concatenate_csv_files(raw_data_directory, processed_file_path)
        else:
            print("No files to transfer over or process")

    finally:
        ssh_client.close()


if __name__ == "__main__":
    main()
