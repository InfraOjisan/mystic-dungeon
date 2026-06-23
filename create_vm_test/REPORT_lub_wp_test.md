# lub_wp_test WordPress VM 構築レポート

作業日: 2026-04-25

## 結果

`homeserverxeon` 上に libvirt/KVM VM `lub_wp_test` を作成し、WordPress が動作する状態まで確認しました。

- VM 名: `lub_wp_test`
- 仮想化基盤: libvirt/KVM (`qemu:///system`)
- VM OS: Ubuntu 24.04 cloud image
- vCPU: 2
- メモリ: 4GB
- ディスク: 10GB (`/var/lib/libvirt/images/lub_wp_test.qcow2`)
- ネットワーク: libvirt `default` NAT
- IP: `192.168.122.50`
- MAC: `52:54:00:24:04:50`
- Autostart: enabled
- WordPress URL: `http://192.168.122.50/`
- WordPress Login: `http://192.168.122.50/wp-login.php`
- WordPress 管理者: `AdminPandalex`
- 管理者パスワード: `.env` 指定値を使用

## インストール内容

- nginx
- MySQL Server
- PHP-FPM / PHP MySQL 関連拡張
- WordPress
- WP-CLI

## 検証結果

`homeserverxeon` から以下を確認済みです。

- `virsh -c qemu:///system dominfo lub_wp_test`
  - `State: running`
  - `CPU(s): 2`
  - `Max memory: 4194304 KiB`
  - `Autostart: enable`
- `virsh -c qemu:///system domifaddr lub_wp_test`
  - `192.168.122.50/24`
- `curl -fsSI http://192.168.122.50/wp-login.php`
  - `HTTP/1.1 200 OK`
- VM 内
  - `nginx`: active
  - `mysql`: active
  - WordPress version: `6.9.4`
  - WordPress user: `AdminPandalex`

## 作成・配置したファイル

ローカル:

- `provision_lub_wp_test.sh`
- `repair_lub_wp_test.sh`
- `REPORT_lub_wp_test.md`

接続先 `homeserverxeon`:

- `/home/pandalex/provision_lub_wp_test.sh`
- `/home/pandalex/repair_lub_wp_test.sh`
- `/home/pandalex/.ssh/lub_wp_test_ed25519`
- `/var/lib/libvirt/images/noble-server-cloudimg-amd64.img`
- `/var/lib/libvirt/images/lub_wp_test.qcow2`
- `/var/lib/libvirt/images/lub_wp_test-seed.iso`

VM 内:

- `/var/www/wordpress`
- `/etc/nginx/sites-available/wordpress`
- `/usr/local/bin/wp`

## 推察して実行した内容

- `.env` は dotenv 形式ではなく日本語メモ形式として解釈しました。
- `.env` の OS `linuntu24.04` は typo とみなし、Ubuntu/Lubuntu 24.04 系として扱いました。
- 指定 ISO `/home/pandalex/lubuntu-24.04.4-desktop-amd64.iso` は存在しましたが、Lubuntu Desktop ISO は対話インストール向けで WordPress 自動構築に不向きなため、Ubuntu 24.04 cloud image を使って cloud-init で自動構築しました。
- `.env` の作業ディレクトリ `/home/pandale/shared` は実在せず、実在する `/home/pandalex/shared` は root 所有で通常ユーザー書き込み不可だったため、転送スクリプトは `/home/pandalex`、VM ディスクは既存 libvirt pool の `/var/lib/libvirt/images` に配置しました。
- VM の IP は既存 VM と重複しない固定 DHCP として `192.168.122.50` を割り当てました。
- 外部公開要件は明記されていなかったため、libvirt default NAT 内の WordPress ホストとして構築しました。`homeserverxeon` からは直接アクセスできます。手元マシンから直接 `192.168.122.50` に経路がない場合は SSH トンネルが必要です。
- VM への保守用に `homeserverxeon` 上で SSH 鍵 `/home/pandalex/.ssh/lub_wp_test_ed25519` を作成し、VM ユーザー `pandalex` に登録しました。
- 初回 cloud-init では WordPress salt 置換時に `sed` が `/` を含むランダム値で失敗しました。VM は起動済みで nginx/mysql も導入済みだったため、`repair_lub_wp_test.sh` で WordPress 設定と nginx vhost を修復し、ローカルの `provision_lub_wp_test.sh` も同じ問題が再発しないよう hex salt 生成へ修正しました。

## アクセス補足

`homeserverxeon` から:

```bash
curl -I http://192.168.122.50/wp-login.php
```

手元マシンから NAT 内 VM に直接到達できない場合:

```bash
ssh -L 8080:192.168.122.50:80 pandalex@homeserverxeon
```

その状態で `http://localhost:8080/wp-login.php` を開くとアクセスできます。
