import paramiko
import os
import stat


def check_login_status(server_address, username, password):
    """
    检查是否能成功登录到服务器。

    参数：
        server_address (str): 服务器地址
        username (str): 用户名
        password (str): 密码

    返回：
        bool: 登录成功返回 True，失败返回 False
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 尝试连接服务器
        client.connect(hostname=server_address, username=username, password=password, timeout=10)
        print(f"成功登录到服务器 {server_address}")
        return True
    except paramiko.AuthenticationException:
        print("认证失败：请检查用户名和密码。")
        return False
    except paramiko.SSHException as ssh_exception:
        print(f"SSH 连接错误: {ssh_exception}")
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        return False
    finally:
        client.close()


# def download_dir(sftp, remote_path, local_path):
#     """
#     从远程目录递归下载内容到本地目录。
#
#     参数：
#         sftp (SFTPClient): SFTP 客户端对象。
#         remote_path (str): 远程路径。
#         local_path (str): 本地路径。
#     """
#     # 确保本地目录存在
#     os.makedirs(local_path, exist_ok=True)
#     try:
#         for item in sftp.listdir_attr(remote_path):
#             remote_item_path = os.path.join(remote_path, item.filename).replace('\\', '/')
#             local_item_path = os.path.join(local_path, item.filename)
#
#             if stat.S_ISDIR(item.st_mode):
#                 # 如果是目录，则递归下载
#                 download_dir(sftp, remote_item_path, local_item_path)
#             else:
#                 # 如果是文件，则直接下载
#                 sftp.get(remote_item_path, local_item_path)
#     except Exception as e:
#         print(f"下载时出错: {e}")
#
#
# def download_folder(server_address, username, password, remote_folder, local_path=None):
#     """
#     从服务器下载整个文件夹或单个文件到指定目录。
#     """
#     transport = None
#     try:
#         # 设置 SFTP 连接
#         transport = paramiko.Transport((server_address, 22))
#         transport.connect(username=username, password=password)
#         sftp = paramiko.SFTPClient.from_transport(transport)
#
#         # 检查远程路径类型
#         remote_stat = sftp.stat(remote_folder)
#         remote_folder_name = os.path.basename(remote_folder.rstrip('/'))
#
#         if local_path is None:
#             local_path = os.getcwd()  # 默认路径为当前目录
#
#         # 确保目标路径存在
#         if not os.path.exists(local_path):
#             os.makedirs(local_path)
#
#         if stat.S_ISDIR(remote_stat.st_mode):
#             # 如果是目录，调用下载目录函数
#             download_dir(sftp, remote_folder, os.path.join(local_path, remote_folder_name))
#             print(f"文件夹 {remote_folder} 已成功下载到 {local_path}")
#         else:
#             # 如果是文件，直接下载文件
#             local_file_path = os.path.join(local_path, remote_folder_name)
#             sftp.get(remote_folder, local_file_path)
#             print(f"文件 {remote_folder} 已成功下载到 {local_path}")
#
#     except Exception as e:
#         print(f"下载出错: {e}")
#     finally:
#         if transport:
#             transport.close()


def compare_and_download(sftp, remote_path, local_path):
    """
    递归对比远程目录和本地目录，仅下载需要的文件。

    参数：
        sftp (SFTPClient): SFTP 客户端对象。
        remote_path (str): 远程路径。
        local_path (str): 本地路径。
    """
    os.makedirs(local_path, exist_ok=True)  # 确保本地目录存在
    try:
        for item in sftp.listdir_attr(remote_path):
            remote_item_path = os.path.join(remote_path, item.filename).replace('\\', '/')
            local_item_path = os.path.join(local_path, item.filename)

            if stat.S_ISDIR(item.st_mode):
                # 如果是目录，递归对比和下载
                compare_and_download(sftp, remote_item_path, local_item_path)
            else:
                # 如果是文件，检查文件大小并决定是否下载
                if os.path.exists(local_item_path):
                    local_file_size = os.path.getsize(local_item_path)
                    remote_file_size = item.st_size
                    if local_file_size == remote_file_size:
                        print(f"文件 {local_item_path} 已存在且大小相同，跳过下载。")
                        continue

                # 下载文件
                print(f"正在下载文件 {remote_item_path} 到 {local_item_path}...")
                sftp.get(remote_item_path, local_item_path)
    except Exception as e:
        print(f"下载时出错: {e}")

def download_folder(server_address, username, password, remote_folder, local_path=None):
    """
    从服务器下载整个文件夹或单个文件到指定目录，仅下载需要更新的文件。

    参数：
        server_address (str): SFTP 服务器地址。
        username (str): 用户名。
        password (str): 密码。
        remote_folder (str): 远程文件夹路径。
        local_path (str): 本地保存路径。
    """
    transport = None
    try:
        # 设置 SFTP 连接
        transport = paramiko.Transport((server_address, 22))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # 检查远程路径类型
        remote_stat = sftp.stat(remote_folder)
        remote_folder_name = os.path.basename(remote_folder.rstrip('/'))

        if local_path is None:
            local_path = os.getcwd()  # 默认路径为当前目录

        # 确保目标路径存在
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        if stat.S_ISDIR(remote_stat.st_mode):
            # 如果是目录，调用递归对比和下载函数
            compare_and_download(sftp, remote_folder, os.path.join(local_path, remote_folder_name))
            print(f"文件夹 {remote_folder} 已成功下载到 {local_path}")
        else:
            # 如果是文件，直接下载文件
            local_file_path = os.path.join(local_path, remote_folder_name)
            if os.path.exists(local_file_path):
                local_file_size = os.path.getsize(local_file_path)
                remote_file_size = remote_stat.st_size
                if local_file_size == remote_file_size:
                    print(f"文件 {local_file_path} 已存在且大小相同，跳过下载。")
                    return

            print(f"正在下载文件 {remote_folder} 到 {local_file_path}...")
            sftp.get(remote_folder, local_file_path)
            print(f"文件 {remote_folder} 已成功下载到 {local_path}")

    except Exception as e:
        print(f"下载出错: {e}")
    finally:
        if transport:
            transport.close()




# 示例用法
if __name__ == "__main__":
    server_address = "23.95.165.138"  # 替换为你的服务器地址
    username = "root"  # 替换为你的服务器用户名
    password = "bF9EIy61h2Juvq6P6L"  # 替换为你的服务器密码
    remote_folder = "/root/coinank/main/data/long_short/"  # 替换为远程文件夹路径

    is_logged_in = check_login_status(server_address, username, password)
    if is_logged_in:
        download_folder(server_address, username, password, remote_folder)
    else:
        print("无法登录到服务器，下载中止。")
