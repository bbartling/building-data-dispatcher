import os
import pandas as pd
import paramiko
from scp import SCPClient

def create_ssh_client(host, port, username, key_file, password=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if password:
            client.connect(hostname=host, port=port, username=username, key_filename=key_file, password=password)
        else:
            client.connect(hostname=host, port=port, username=username, key_filename=key_file)
        
        print("SSH login successful!")  # Print the success message
        return client
    except paramiko.AuthenticationException:
        print("SSH login failed. Check your credentials and key file.")
        raise

def list_csv_files(ssh_client, remote_path):
    stdin, stdout, stderr = ssh_client.exec_command(f'ls {remote_path}/*.csv')
    # Return each line as a string, stripping any whitespace
    return [line.strip() for line in stdout]

def scp_files(ssh_client, remote_files, local_path):
    # Create raw_data directory if it doesn't exist
    os.makedirs(os.path.join(local_path, 'raw_data'), exist_ok=True)

    with SCPClient(ssh_client.get_transport()) as scp:
        for file in remote_files:
            # Change the local file path to save in raw_data directory
            local_file_path = os.path.join(local_path, 'raw_data', os.path.basename(file))
            scp.get(file, local_file_path)
            process_csv(local_file_path)

def process_csv(file_path):
    # Read the CSV data, skipping any duplicated header row
    df = pd.read_csv(file_path, skiprows=lambda x: x == 1)

    # Convert 'Time' to datetime, coercing errors to NaT
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce', format='%Y-%m-%dT%H:%M:%S.%f')

    # Keep only rows where 'Time' is not NaT
    df = df[df['Time'].notna()]

    # Check for duplicates and handle them if necessary
    df = df.drop_duplicates(subset=['Time', 'Point Name'], keep='first')

    # Pivot the table to get unique columns for each point name
    pivoted_df = df.pivot(index='Time', columns='Point Name', values='Value')

    # Forward fill and then backfill the gaps
    pivoted_df = pivoted_df.ffill().bfill()

    # Create processed_data directory if it doesn't exist
    processed_directory = 'processed_data'
    os.makedirs(processed_directory, exist_ok=True)

    # Save to a new CSV file in the processed_data subdirectory
    processed_file_name = os.path.splitext(os.path.basename(file_path))[0] + '_processed.csv'
    processed_file_path = os.path.join(processed_directory, processed_file_name)
    pivoted_df.to_csv(processed_file_path)

    print(f"Processed file saved as: {processed_file_path}")
    print(df)

def main():
    host = '192.168.0.113'
    port = 22  # default SSH port
    username = 'user'
    key_file = r'C:\Users\bbartling\.ssh\asdf.pub'
    remote_path = '/home/project/building/data'
    local_path = './'
    password = 'admin'

    # Create SSH client and connect with password
    ssh_client = create_ssh_client(host, port, username, key_file, password=password)

    try:
        # List CSV files on Raspberry Pi
        remote_files = list_csv_files(ssh_client, remote_path)
        print("remote_files \n",remote_files)

        # Compare with local files and decide which files to transfer
        files_to_transfer = [file for file in remote_files if 'bacnet_data.csv' in file]
        print("files_to_transfer \n",files_to_transfer)

        # SCP the files and process them
        scp_files(ssh_client, files_to_transfer, local_path)

    finally:
        ssh_client.close()

if __name__ == '__main__':
    main()
