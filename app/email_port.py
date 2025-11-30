"""
EmailPort - Email service interface Gateway để giao tiếp với dịch vụ email ngoài
Class cổng để xử lý việc gửi email qua SMTP
"""
import asyncio
from datetime import datetime
from email.message import EmailMessage
from typing import Optional
import aiosmtplib
from jose import jwt, JWTError
from configs.config_mail import mail_settings
from app.config import settings


class EmailPort:
    """
    Email service interface Gateway để giao tiếp với dịch vụ email ngoài
    
    Quản lý việc gửi email qua SMTP với các template HTML đẹp
    """
    
    def __init__(self):
        self.service_name = "Auction System Email Service"
        self.default_from_name = mail_settings.MAIL_FROM_NAME
        self.default_from_address = mail_settings.MAIL_FROM_ADDRESS
        self.support_email = mail_settings.SUPPORT_EMAIL
        
    def get_service_status(self) -> dict:
        """
        Kiểm tra trạng thái dịch vụ email
        """
        return {
            "service_status": "active",
            "service_name": self.service_name,
            "smtp_host": mail_settings.MAIL_HOST,
            "smtp_port": mail_settings.MAIL_PORT,
            "tls_enabled": mail_settings.MAIL_USE_TLS,
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def send_raw_email(
        self,
        subject: str,
        content: str,
        target_address: str,
        is_html: bool = True,
        from_name: str = None,
        from_address: str = None
    ) -> dict:
        """
        Gateway endpoint: Gửi email thô qua SMTP
        
        Args:
            subject: Tiêu đề email
            content: Nội dung email (HTML hoặc text)
            target_address: Địa chỉ người nhận
            is_html: Định dạng HTML hay text
            from_name: Tên người gửi (optional)
            from_address: Địa chỉ người gửi (optional)
        
        Returns:
            dict: Kết quả gửi email với success status và message
        """
        try:
            message = EmailMessage()
            message["From"] = f"{from_name or self.default_from_name} <{from_address or self.default_from_address}>"
            message["To"] = target_address
            message["Subject"] = subject
            message["Date"] = datetime.now()
            
            if is_html:
                message.set_content(content, subtype="html")
            else:
                message.set_content(content)
            
            await aiosmtplib.send(
                message,
                hostname=mail_settings.MAIL_HOST,
                port=mail_settings.MAIL_PORT,
                start_tls=mail_settings.MAIL_USE_TLS,
                username=mail_settings.MAIL_USERNAME,
                password=mail_settings.MAIL_PASSWORD,
                timeout=mail_settings.MAIL_TIMEOUT
            )
            
            print(f"Email sent successfully to {target_address}")
            return {
                "success": True,
                "message": f"Email sent successfully to {target_address}",
                "recipient": target_address,
                "sent_at": datetime.utcnow().isoformat(),
                "service": self.service_name
            }
            
        except Exception as e:
            error_msg = f"Failed to send email to {target_address}: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "recipient": target_address,
                "error_type": type(e).__name__,
                "sent_at": datetime.utcnow().isoformat(),
                "service": self.service_name
            }
    
    async def send_otp_email(
        self,
        otp: str,
        username: str,
        target_address: str,
        request_type: str = "registration"
    ) -> dict:
        """
        Gateway endpoint: Gửi email OTP xác minh
        
        Args:
            otp: Mã OTP 6 chữ số
            username: Tên người dùng
            target_address: Địa chỉ email
            request_type: Loại yêu cầu (registration, password_reset, email_change)
        
        Returns:
            dict: Kết quả gửi email
        """
        
        # Định nghĩa message dựa trên loại request
        if request_type == "registration":
            subject = "Xác minh email đăng ký tài khoản - Auction System"
            greeting = f"Xin chào {username}!"
            purpose_msg = (
                "Cảm ơn bạn đã đăng ký tài khoản tại Auction System. "
                "Để hoàn tất quá trình đăng ký, vui lòng sử dụng mã xác minh bên dưới:"
            )
            warning_msg = "Mã này sẽ hết hạn sau 5 phút vì lý do bảo mật."
            
        elif request_type == "password_reset":
            subject = "Khôi phục mật khẩu - Auction System"
            greeting = f"Xin chào {username}!"
            purpose_msg = (
                "Chúng tôi đã nhận được yêu cầu khôi phục mật khẩu cho tài khoản của bạn. "
                "Sử dụng mã xác minh bên dưới để tiếp tục quá trình khôi phục:"
            )
            warning_msg = "Nếu bạn không yêu cầu khôi phục mật khẩu, vui lòng bỏ qua email này."
            
        elif request_type == "email_change":
            subject = "Xác minh thay đổi email - Auction System"
            greeting = f"Xin chào {username}!"
            purpose_msg = (
                "Bạn đã yêu cầu thay đổi địa chỉ email. "
                "Sử dụng mã xác minh bên dưới để xác nhận thay đổi:"
            )
            warning_msg = "Nếu bạn không thực hiện thay đổi này, vui lòng liên hệ hỗ trợ ngay lập tức."
            
        else:
            subject = "Mã xác minh - Auction System"
            greeting = f"Xin chào {username}!"
            purpose_msg = "Vui lòng sử dụng mã xác minh bên dưới:"
            warning_msg = "Mã này sẽ hết hạn sau 5 phút."
        
        # Template HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">
                                        Auction System
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <!-- Greeting -->
                                    <p style="font-size: 18px; color: #333333; margin: 0 0 20px 0; line-height: 1.5;">
                                        {greeting}
                                    </p>
                                    
                                    <!-- Purpose Message -->
                                    <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                        {purpose_msg}
                                    </p>
                                    
                                    <!-- OTP Code Box -->
                                    <div style="text-align: center; margin: 40px 0;">
                                        <div style="display: inline-block; background-color: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; min-width: 200px;">
                                            <p style="font-size: 14px; color: #6c757d; margin: 0 0 10px 0; font-weight: 500;">
                                                Mã xác minh của bạn:
                                            </p>
                                            <h2 style="font-family: 'Courier New', monospace; font-size: 32px; color: #495057; margin: 0; letter-spacing: 8px; font-weight: bold;">
                                                {otp}
                                            </h2>
                                        </div>
                                    </div>
                                    
                                    <!-- Warning -->
                                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 30px 0;">
                                        <p style="font-size: 14px; color: #856404; margin: 0; line-height: 1.5;">
                                            <strong>Lưu ý quan trọng:</strong><br>
                                            {warning_msg}<br>
                                            <strong>KHÔNG chia sẻ mã này với bất kỳ ai, kể cả nhân viên hỗ trợ.</strong>
                                        </p>
                                    </div>
                                    
                                    <!-- Footer -->
                                    <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 40px;">
                                        <p style="font-size: 12px; color: #6c757d; margin: 0 0 10px 0; line-height: 1.4;">
                                            Nếu bạn có bất kỳ câu hỏi nào, vui lòng liên hệ với đội ngũ hỗ trợ tại {self.support_email}
                                        </p>
                                        <p style="font-size: 12px; color: #6c757d; margin: 0; line-height: 1.4;">
                                            Email này được gửi tự động, vui lòng không trả lời email này.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer Strip -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                                    <p style="font-size: 12px; color: #6c757d; margin: 0;">
                                        © 2024 Auction System. Tất cả quyền được bảo lưu.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return await self.send_raw_email(subject, html_content, target_address, is_html=True)
    
    async def send_welcome_email(self, username: str, email: str) -> dict:
        """
        Gateway endpoint: Gửi email chào mừng sau khi đăng ký thành công
        
        Args:
            username: Tên người dùng
            email: Địa chỉ email
        
        Returns:
            dict: Kết quả gửi email
        """
        
        subject = "Chào mừng đến với Auction System!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">
                                        Chào mừng đến với Auction System!
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px; text-align: center;">
                                    <h2 style="font-size: 20px; color: #333333; margin: 0 0 20px 0;">
                                        Xin chào {username}!
                                    </h2>
                                    
                                    <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                        Cảm ơn bạn đã đăng ký tài khoản tại Auction System. 
                                        Email của bạn đã được xác minh thành công và tài khoản đã được kích hoạt.
                                    </p>
                                    
                                    <div style="background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; padding: 20px; margin: 30px 0;">
                                        <p style="font-size: 14px; color: #1565c0; margin: 0; line-height: 1.5;">
                                            <strong>Bây giờ bạn có thể:</strong><br>
                                            • Đăng nhập vào tài khoản<br>
                                            • Tham gia đấu giá sản phẩm<br>
                                            • Đặt giá thầu và giành chiến thắng<br>
                                            • Quản lý thông tin cá nhân
                                        </p>
                                    </div>
                                    
                                    <p style="font-size: 14px; color: #666666; margin: 30px 0 20px 0; line-height: 1.6;">
                                        Nếu bạn có bất kỳ câu hỏi nào, đừng ngần ngại liên hệ với chúng tôi.
                                    </p>
                                    
                                    <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px;">
                                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                                            Trân trọng,<br>
                                            Đội ngũ Auction System
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return await self.send_raw_email(subject, html_content, email, is_html=True)

    async def send_payment_email(
        self,
        username: str,
        email: str,
        auction_name: str,
        amount: int,
        qr_url: str,
        expires_at: datetime,
        email_type: str = "deposit"
    ) -> dict:
        """
        Gateway endpoint: Gửi email thanh toán (đặt cọc hoặc thanh toán cuối)
        
        Args:
            username: Tên người dùng
            email: Địa chỉ email
            auction_name: Tên phiên đấu giá
            amount: Số tiền
            qr_url: URL QR code
            expires_at: Thời gian hết hạn
            email_type: Loại email ("deposit" hoặc "final_payment")
        
        Returns:
            dict: Kết quả gửi email
        """
        
        if email_type == "deposit":
            return await self._send_deposit_email(username, email, auction_name, amount, qr_url, expires_at)
        else:
            return await self._send_final_payment_email(username, email, auction_name, amount, qr_url, expires_at)
    
    async def _send_deposit_email(self, username: str, email: str, auction_name: str, 
                                deposit_amount: int, qr_url: str, expires_at: datetime) -> dict:
        """
        Gửi email đặt cọc
        """
        subject = f"Thanh toán đặt cọc tham gia đấu giá - {auction_name}"
        remaining_minutes = int((expires_at - datetime.utcnow()).total_seconds() / 60)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">
                                        Thanh toán đặt cọc tham gia đấu giá
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <p style="font-size: 18px; color: #333333; margin: 0 0 20px 0; line-height: 1.5;">
                                        Xin chào {username}!
                                    </p>
                                    
                                    <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0;">
                                        <h3 style="font-size: 18px; color: #333333; margin: 0 0 15px 0;">
                                            {auction_name}
                                        </h3>
                                        <p style="font-size: 16px; color: #495057; margin: 0; font-weight: bold;">
                                            Số tiền đặt cọc: <span style="color: #dc3545;">{deposit_amount:,} VND</span>
                                        </p>
                                    </div>
                                    
                                    <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                        Để hoàn tất đăng ký tham gia đấu giá, vui lòng thực hiện thanh toán đặt cọc 
                                        trong thời gian quy định.
                                    </p>
                                    
                                    <div style="text-align: center; margin: 30px 0;">
                                        <p style="font-size: 14px; color: #666666; margin: 20px 0;">
                                            <a href="{qr_url}" style="color: #007bff; text-decoration: none;">Click vào đây để thanh toán trên web</a>
                                        </p>
                                    </div>
                                    
                                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 30px 0;">
                                        <p style="font-size: 14px; color: #856404; margin: 0; line-height: 1.5;">
                                            <strong>⚠️ QUAN TRỌNG:</strong><br>
                                            Mã thanh toán sẽ hết hạn sau <span style="font-weight: bold;">{remaining_minutes} phút</span>!
                                        </p>
                                    </div>
                                    
                                    <p style="font-size: 12px; color: #6c757d; margin: 0 0 10px 0; line-height: 1.4;">
                                        Liên hệ hỗ trợ: {self.support_email}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return await self.send_raw_email(subject, html_content, email, is_html=True)
    
    async def _send_final_payment_email(self, username: str, email: str, auction_name: str, 
                                       final_amount: int, qr_url: str, expires_at: datetime) -> dict:
        """
        Gửi email thanh toán cuối
        """
        subject = f"🎉 Chúc mừng! Bạn đã thắng đấu giá - {auction_name}"
        remaining_hours = int((expires_at - datetime.utcnow()).total_seconds() / 3600)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">
                                        🎉 Chúc mừng! Bạn đã thắng đấu giá
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                                        <h2 style="font-size: 24px; color: #155724; margin: 0 0 15px 0;">
                                            Xin chúc mừng {username}!
                                        </h2>
                                    </div>
                                    
                                    <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0;">
                                        <h3 style="font-size: 18px; color: #333333; margin: 0 0 15px 0;">
                                            {auction_name}
                                        </h3>
                                        <p style="font-size: 16px; color: #495057; margin: 0; font-weight: bold;">
                                            Số tiền thanh toán: <span style="color: #28a745;">{final_amount:,} VND</span>
                                        </p>
                                    </div>
                                    
                                    <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                        Để hoàn tất giao dịch, vui lòng thực hiện thanh toán số tiền còn lại 
                                        trong vòng 24 giờ.
                                    </p>
                                    
                                    <div style="text-align: center; margin: 30px 0;">
                                        <p style="font-size: 14px; color: #666666; margin: 20px 0;">
                                            <a href="{qr_url}" style="color: #007bff; text-decoration: none;">Click vào đây để thanh toán trên web</a>
                                        </p>
                                    </div>
                                    
                                    <div style="background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; padding: 15px; margin: 30px 0;">
                                        <p style="font-size: 14px; color: #1565c0; margin: 0; line-height: 1.5;">
                                            <strong>⏰ Thời hạn thanh toán:</strong><br>
                                            Mã thanh toán có hiệu lực trong <span style="font-weight: bold;">{remaining_hours} giờ</span>.
                                        </p>
                                    </div>
                                    
                                    <p style="font-size: 12px; color: #6c757d; margin: 0 0 10px 0; line-height: 1.4;">
                                        Liên hệ hỗ trợ: {self.support_email}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return await self.send_raw_email(subject, html_content, email, is_html=True)
    
    async def send_payment_confirmation_email(
        self,
        username: str,
        email: str,
        auction_name: str,
        payment_amount: int,
        payment_type: str,
        payment_method: str = "bank_transfer"
    ) -> dict:
        """
        Gateway endpoint: Gửi email xác nhận thanh toán thành công
        
        Args:
            username: Tên người dùng
            email: Địa chỉ email
            auction_name: Tên phiên đấu giá
            payment_amount: Số tiền đã thanh toán
            payment_type: Loại thanh toán ("deposit" hoặc "final_payment")
            payment_method: Phương thức thanh toán
        
        Returns:
            dict: Kết quả gửi email
        """
        
        if payment_type == "deposit":
            subject = f"✅ Xác nhận thanh toán đặt cọc thành công - {auction_name}"
            payment_type_text = "Đặt cọc tham gia đấu giá"
            next_steps = "Bây giờ bạn có thể bắt đầu đặt giá thầu cho phiên đấu giá này!"
        else:
            subject = f"🎉 Xác nhận thanh toán thành công - {auction_name}"
            payment_type_text = "Thanh toán đấu giá"
            next_steps = "Chúng tôi sẽ liên hệ trong 24 giờ để sắp xếp việc giao hàng."
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">
                                        {subject}
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px; text-align: center;">
                                    <div style="margin: 0 0 30px 0;">
                                        <div style="width: 80px; height: 80px; background-color: #28a745; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 40px; color: white;">
                                            ✓
                                        </div>
                                    </div>
                                    
                                    <h2 style="font-size: 24px; color: #333333; margin: 0 0 20px 0;">
                                        Xin chúc mừng {username}!
                                    </h2>
                                    
                                    <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                        Chúng tôi đã nhận được thanh toán của bạn một cách thành công.
                                    </p>
                                    
                                    <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 25px; margin: 30px 0; text-align: left;">
                                        <h3 style="font-size: 18px; color: #333333; margin: 0 0 20px 0; text-align: center;">
                                            Chi tiết thanh toán
                                        </h3>
                                        
                                        <table style="width: 100%;">
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6c757d; width: 40%;">
                                                    Loại thanh toán:
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #333333; font-weight: bold;">
                                                    {payment_type_text}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6c757d;">
                                                    Sản phẩm đấu giá:
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #333333; font-weight: bold;">
                                                    {auction_name}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6c757d;">
                                                    Số tiền:
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #28a745; font-weight: bold; font-size: 16px;">
                                                    {payment_amount:,} VND
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6c757d;">
                                                    Phương thức thanh toán:
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #333333;">
                                                    {payment_method}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6c757d;">
                                                    Thời gian thanh toán:
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #333333;">
                                                    {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S UTC')}
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <div style="background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; padding: 20px; margin: 30px 0;">
                                        <p style="font-size: 14px; color: #1565c0; margin: 0; line-height: 1.5;">
                                            <strong>Bước tiếp theo:</strong><br>
                                            {next_steps}
                                        </p>
                                    </div>
                                    
                                    <p style="font-size: 14px; color: #666666; margin: 30px 0 20px 0; line-height: 1.6;">
                                        Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi.
                                    </p>
                                    
                                    <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px;">
                                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                                            Trân trọng,<br>
                                            Đội ngũ Auction System
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return await self.send_raw_email(subject, html_content, email, is_html=True)


# Khởi tạo instance global để sử dụng trong toàn bộ ứng dụng
email_port = EmailPort()
