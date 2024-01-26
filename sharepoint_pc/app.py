import os
import pandas as pd
import paramiko
from scp import SCPClient

def create_ssh_client(host, port, username, key_file):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=username, key_filename=key_file)
    return client

def list_csv_files(ssh_client, remote_path):
    stdin, stdout, stderr = ssh_client.exec_command(f'ls {remote_path}/*.csv')
    return stdout.read().splitlines()

def scp_files(ssh_client, remote_files, local_path):
    with SCPClient(ssh_client.get_transport()) as scp:
        for file in remote_files:
            scp.get(file, local_path)
            process_csv(os.path.join(local_path, os.path.basename(file)))

def process_csv(file_path):
    # Read the CSV data
    df = pd.read_csv(file_path)

    # Pivot the table to get unique columns for each point name
    pivoted_df = df.pivot(index='Time', columns='Point Name', values='Value')

    # Optionally, fill NaN values if needed
    # pivoted_df.fillna(0, inplace=True)

    # Save to a new CSV file
    processed_file_path = os.path.splitext(file_path)[0] + '_processed.csv'
    pivoted_df.to_csv(processed_file_path)
    print(f"Processed file saved as: {processed_file_path}")

def main():
    host = 'your_raspberry_pi_ip'
    port = 22  # default SSH port
    username = 'your_username'
    key_file = '/path/to/ssh/key'
    remote_path = '/remote/csv/directory'
    local_path = '/local/csv/directory'

    # Create SSH client and connect
    ssh_client = create_ssh_client(host, port, username, key_file)

    try:
        # List CSV files on Raspberry Pi
        remote_files = list_csv_files(ssh_client, remote_path)

        # Compare with local files and decide which files to transfer
        files_to_transfer = [file for file in remote_files if not os.path.exists(os.path.join(local_path, os.path.basename(file)))]

        # SCP the files and process them
        scp_files(ssh_client, files_to_transfer, local_path)

    finally:
        ssh_client.close()

if __name__ == '__main__':
    main()
