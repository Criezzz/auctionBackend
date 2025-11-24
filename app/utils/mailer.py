"""
Email utilities for sending HTML emails with OTP codes
"""
import asyncio
from datetime import datetime
from email.message import EmailMessage
from typing import Optional
import aiosmtplib
from jose import jwt, JWTError
from configs.config_mail import mail_settings
from app.config import settings


async def send_email(
    subject: str,
    content: str,
    target_address: str,
    is_html: bool = True
) -> bool:
    """
    Send email using SMTP configuration
    
    Args:
        subject: Email subject line
        content: Email body content (HTML or plain text)
        target_address: Recipient email address
        is_html: Whether content is HTML formatted
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        message = EmailMessage()
        message["From"] = f"{mail_settings.MAIL_FROM_NAME} <{mail_settings.MAIL_FROM_ADDRESS}>"
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
        return True
        
    except Exception as e:
        print(f"Failed to send email to {target_address}: {str(e)}")
        return False


async def send_otp_email(
    otp: str,
    username: str,
    target_address: str,
    request_type: str = "registration"
) -> bool:
    """
    Send OTP verification email with HTML template
    
    Args:
        otp: 6-digit OTP code
        username: Target username
        target_address: Recipient email address
        request_type: Type of request (registration, password_reset, email_change)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    # Define message based on request type
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
    
    # HTML template with inline CSS
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
                                        Nếu bạn có bất kỳ câu hỏi nào, vui lòng liên hệ với đội ngũ hỗ trợ tại {mail_settings.SUPPORT_EMAIL}
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
    
    # Send email
    return await send_email(subject, html_content, target_address, is_html=True)


async def send_welcome_email(username: str, email: str) -> bool:
    """
    Send welcome email after successful registration
    
    Args:
        username: Target username
        email: Recipient email address
    
    Returns:
        bool: True if email sent successfully, False otherwise
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
    

async def send_deposit_email(
    username: str,
    email: str,
    auction_name: str,
    deposit_amount: int,
    qr_url: str,
    expires_at: datetime
) -> bool:
    """
    Send deposit payment email for auction registration
    
    Args:
        username: Target username
        email: Recipient email address
        auction_name: Name of the auction
        deposit_amount: Deposit amount in VND
        qr_url: QR code URL for payment
        expires_at: Token expiration datetime
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    subject = f"Thanh toán đặt cọc tham gia đấu giá - {auction_name}"
    
    # Calculate remaining time
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
                                <!-- Greeting -->
                                <p style="font-size: 18px; color: #333333; margin: 0 0 20px 0; line-height: 1.5;">
                                    Xin chào {username}!
                                </p>
                                
                                <!-- Auction Info -->
                                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0;">
                                    <p style="font-size: 14px; color: #6c757d; margin: 0 0 10px 0; font-weight: 500;">
                                        Thông tin đấu giá:
                                    </p>
                                    <h3 style="font-size: 18px; color: #333333; margin: 0 0 15px 0;">
                                        {auction_name}
                                    </h3>
                                    <p style="font-size: 16px; color: #495057; margin: 0; font-weight: bold;">
                                        Số tiền đặt cọc: <span style="color: #dc3545;">{deposit_amount:,} VND</span>
                                    </p>
                                </div>
                                
                                <!-- Purpose Message -->
                                <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                    Để hoàn tất đăng ký tham gia đấu giá, vui lòng thực hiện thanh toán đặt cọc 
                                    trong thời gian quy định. Sau khi thanh toán thành công, bạn sẽ có thể bắt đầu đặt giá thầu.
                                </p>
                                
                                <!-- QR Code Section -->
                                <div style="text-align: center; margin: 30px 0;">
                                    <h4 style="font-size: 16px; color: #333333; margin: 0 0 15px 0;">
                                        Quét mã QR để thanh toán nhanh:
                                    </h4>
                                    
                                    <!-- QR Placeholder -->
                                    <div style="background-color: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px; padding: 30px; margin: 20px 0; display: inline-block;">
                                        <div style="width: 150px; height: 150px; background-color: #ffffff; border: 1px solid #dee2e6; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #6c757d; text-align: center;">
                                            QR Code<br>{qr_url}
                                        </div>
                                    </div>
                                    
                                    <!-- Alternative Payment -->
                                    <p style="font-size: 14px; color: #666666; margin: 20px 0;">
                                        Hoặc <a href="{qr_url}" style="color: #007bff; text-decoration: none;">click vào đây</a> để thanh toán trên web
                                    </p>
                                </div>
                                
                                <!-- Expiry Warning -->
                                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 30px 0;">
                                    <p style="font-size: 14px; color: #856404; margin: 0; line-height: 1.5;">
                                        <strong>⚠️ QUAN TRỌNG:</strong><br>
                                        Mã thanh toán sẽ hết hạn sau <span style="font-weight: bold;">{remaining_minutes} phút</span>!<br>
                                        Vui lòng hoàn thành thanh toán trước khi hết hạn.
                                    </p>
                                </div>
                                
                                <!-- Instructions -->
                                <div style="background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; padding: 20px; margin: 30px 0;">
                                    <p style="font-size: 14px; color: #1565c0; margin: 0; line-height: 1.5;">
                                        <strong>Hướng dẫn thanh toán:</strong><br>
                                        1. Quét mã QR hoặc click link bên trên<br>
                                        2. Chọn phương thức thanh toán ưa thích<br>
                                        3. Nhập thông tin cần thiết<br>
                                        4. Xác nhận và hoàn thành giao dịch<br>
                                        5. Đợi email xác nhận thanh toán thành công
                                    </p>
                                </div>
                                
                                <!-- Footer -->
                                <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 40px;">
                                    <p style="font-size: 12px; color: #6c757d; margin: 0 0 10px 0; line-height: 1.4;">
                                        Nếu bạn có bất kỳ câu hỏi nào, vui lòng liên hệ với đội ngũ hỗ trợ tại {mail_settings.SUPPORT_EMAIL}
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
    
    return await send_email(subject, html_content, email, is_html=True)


async def send_payment_email(
    username: str,
    email: str,
    auction_name: str,
    final_amount: int,
    qr_url: str,
    expires_at: datetime
) -> bool:
    """
    Send final payment email for won auction
    
    Args:
        username: Target username
        email: Recipient email address
        auction_name: Name of the won auction
        final_amount: Final payment amount in VND
        qr_url: QR code URL for payment
        expires_at: Token expiration datetime
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    subject = f"🎉 Chúc mừng! Bạn đã thắng đấu giá - {auction_name}"
    
    # Calculate remaining time in hours
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
                                <!-- Congratulations -->
                                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                                    <h2 style="font-size: 24px; color: #155724; margin: 0 0 15px 0;">
                                        Xin chúc mừng {username}!
                                    </h2>
                                    <p style="font-size: 16px; color: #155724; margin: 0;">
                                        Bạn đã thành công giành chiến thắng trong phiên đấu giá này
                                    </p>
                                </div>
                                
                                <!-- Auction Info -->
                                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0;">
                                    <p style="font-size: 14px; color: #6c757d; margin: 0 0 10px 0; font-weight: 500;">
                                        Thông tin đấu giá:
                                    </p>
                                    <h3 style="font-size: 18px; color: #333333; margin: 0 0 15px 0;">
                                        {auction_name}
                                    </h3>
                                    <p style="font-size: 16px; color: #495057; margin: 0; font-weight: bold;">
                                        Số tiền thanh toán: <span style="color: #28a745;">{final_amount:,} VND</span>
                                    </p>
                                </div>
                                
                                <!-- Payment Request -->
                                <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                    Để hoàn tất giao dịch, vui lòng thực hiện thanh toán số tiền còn lại 
                                    trong vòng 24 giờ. Sau khi thanh toán thành công, chúng tôi sẽ liên hệ 
                                    để sắp xếp việc giao hàng.
                                </p>
                                
                                <!-- QR Code Section -->
                                <div style="text-align: center; margin: 30px 0;">
                                    <h4 style="font-size: 16px; color: #333333; margin: 0 0 15px 0;">
                                        Quét mã QR để thanh toán nhanh:
                                    </h4>
                                    
                                    <!-- QR Placeholder -->
                                    <div style="background-color: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px; padding: 30px; margin: 20px 0; display: inline-block;">
                                        <div style="width: 150px; height: 150px; background-color: #ffffff; border: 1px solid #dee2e6; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #6c757d; text-align: center;">
                                            QR Code<br>{qr_url}
                                        </div>
                                    </div>
                                    
                                    <!-- Alternative Payment -->
                                    <p style="font-size: 14px; color: #666666; margin: 20px 0;">
                                        Hoặc <a href="{qr_url}" style="color: #007bff; text-decoration: none;">click vào đây</a> để thanh toán trên web
                                    </p>
                                </div>
                                
                                <!-- Expiry Notice -->
                                <div style="background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; padding: 15px; margin: 30px 0;">
                                    <p style="font-size: 14px; color: #1565c0; margin: 0; line-height: 1.5;">
                                        <strong>⏰ Thời hạn thanh toán:</strong><br>
                                        Mã thanh toán có hiệu lực trong <span style="font-weight: bold;">{remaining_hours} giờ</span>.<br>
                                        Vui lòng hoàn thành thanh toán trước hạn để đảm bảo quyền lợi của bạn.
                                    </p>
                                </div>
                                
                                <!-- Next Steps -->
                                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 20px; margin: 30px 0;">
                                    <p style="font-size: 14px; color: #856404; margin: 0; line-height: 1.5;">
                                        <strong>Quy trình tiếp theo:</strong><br>
                                        1. Thanh toán số tiền còn lại<br>
                                        2. Đợi email xác nhận thanh toán<br>
                                        3. Đội ngũ hỗ trợ sẽ liên hệ trong 24h<br>
                                        4. Xác nhận thông tin giao hàng<br>
                                        5. Nhận hàng và hoàn tất giao dịch
                                    </p>
                                </div>
                                
                                <!-- Footer -->
                                <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 40px;">
                                    <p style="font-size: 12px; color: #6c757d; margin: 0 0 10px 0; line-height: 1.4;">
                                        Nếu bạn có bất kỳ câu hỏi nào, vui lòng liên hệ với đội ngũ hỗ trợ tại {mail_settings.SUPPORT_EMAIL}
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
    
    return await send_email(subject, html_content, email, is_html=True)


async def send_payment_confirmation_email(
    username: str,
    email: str,
    auction_name: str,
    payment_amount: int,
    payment_type: str,  # "deposit" or "final_payment"
    payment_method: str = "bank_transfer"
) -> bool:
    """
    Send payment confirmation email after successful payment
    
    Args:
        username: Target username
        email: Recipient email address
        auction_name: Name of the auction
        payment_amount: Confirmed payment amount in VND
        payment_type: "deposit" or "final_payment"
        payment_method: Payment method used
    
    Returns:
        bool: True if email sent successfully, False otherwise
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
                                <!-- Success Icon -->
                                <div style="margin: 0 0 30px 0;">
                                    <div style="width: 80px; height: 80px; background-color: #28a745; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 40px; color: white;">
                                        ✓
                                    </div>
                                </div>
                                
                                <!-- Success Message -->
                                <h2 style="font-size: 24px; color: #333333; margin: 0 0 20px 0;">
                                    Xin chúc mừng {username}!
                                </h2>
                                
                                <p style="font-size: 16px; color: #666666; margin: 0 0 30px 0; line-height: 1.6;">
                                    Chúng tôi đã nhận được thanh toán của bạn một cách thành công.
                                </p>
                                
                                <!-- Payment Details -->
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
                                
                                <!-- Next Steps -->
                                <div style="background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; padding: 20px; margin: 30px 0;">
                                    <p style="font-size: 14px; color: #1565c0; margin: 0; line-height: 1.5;">
                                        <strong>Bước tiếp theo:</strong><br>
                                        {next_steps}
                                    </p>
                                </div>
                                
                                <!-- Contact Info -->
                                <p style="font-size: 14px; color: #666666; margin: 30px 0 20px 0; line-height: 1.6;">
                                    Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi. Nếu có bất kỳ câu hỏi nào, 
                                    đừng ngần ngại liên hệ với đội ngũ hỗ trợ.
                                </p>
                                
                                <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px;">
                                    <p style="font-size: 12px; color: #6c757d; margin: 0;">
                                        Trân trọng,<br>
                                        Đội ngũ Auction System
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
    
    return await send_email(subject, html_content, email, is_html=True)