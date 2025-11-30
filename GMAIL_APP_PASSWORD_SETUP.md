# Gmail App Password Setup Guide

## Van de hien tai
Khi dang ky tai khoan, he thong bao loi:
```
(534, '5.7.9 Application-specific password required. 
For more information, go to
5.7.9  https://support.google.com/mail/?p=InvalidSecondFactor d9443c01a7336-29bceb55192sm75317325ad.91 - gsmtp')
```

## Nguyen nhan
Gmail yeu cau "Application-specific password" thay vi regular password de gui email qua SMTP.

## Giai quyet

### Buoc 1: Dang nhap Gmail
1. Vao https://mail.google.com
2. Dang nhap tai khoan: `namtotet205@gmail.com`

### Buoc 2: Bat 2-Step Verification
1. Vao https://myaccount.google.com/security
2. Trong muc "Dang nhap vao Google", click "2-Step Verification"
3. Neu chua bat, click "Bat" va lam theo huong dan
4. Neu da bat, chuyen sang buoc 3

### Buoc 3: Tao App Password
1. Vao https://myaccount.google.com/apppasswords
2. Chon "Mail" trong dropdown
3. Click "Generate"
4. Copy 16-character code (dang: xxxx xxxx xxxx xxxx)

### Buoc 4: Cap nhat .env
1. Mo file `.env` trong project
2. Tim dong: `MAIL_PASSWORD=@`
3. Thay the bang App Password vua tao
4. Luu file

### Buoc 5: Test
1. Chay lai test registration
2. Kiem tra email namtotet205@gmail.com

## Ma hoa
- **App Password**: 16-character code khong co khoang trang
- **Vi du**: `abcd1234efgh5678`
- **Khong phai**: regular password

## Luu y
- App Password chi su dung duy nhat cho Mail app
- Neu mat App Password, co the tao lai trong Google Account settings
- App Password van hoat dong neu doi mat khau Gmail