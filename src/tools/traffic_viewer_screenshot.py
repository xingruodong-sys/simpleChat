import asyncio
import argparse
from datetime import datetime
import os
from playwright.async_api import async_playwright
import time

async def capture_traffic_screenshot(latitude, longitude, utc_time, output_path="screenshot.png", headless=False):
    """
    使用Playwright访问HERE Traffic Viewer，输入坐标和时间，并截图
    
    参数:
        latitude (float): 纬度
        longitude (float): 经度
        utc_time (str): UTC时间，格式为 "YYYY-MM-DD HH:MM:SS"
        output_path (str): 截图保存路径
        headless (bool): 是否使用无头模式运行浏览器
    """
    print(f"正在启动浏览器访问 HERE Traffic Viewer...")
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # 访问网站
        print(f"正在访问 https://trafficviewer.ext.here.com/index.html")
        await page.goto("https://trafficviewer.ext.here.com/index.html")
        
        # 等待页面加载完成
        await page.wait_for_load_state("networkidle")
        print("页面已加载")
        
        # 处理登录
        print("正在登录...")
        # 等待登录表单出现
        await page.wait_for_selector("input[type='text']", state="visible")
        
        # 输入邮箱
        await page.fill("input[type='text']", "zhou.hy@neusoft.com")
        
        # 等待密码输入框出现
        await page.wait_for_selector("input[type='password']", state="visible")
        
        # 输入密码
        await page.fill("input[type='password']", "1qaz!QAZ")
        
        # 点击登录按钮 - 修复点击问题
        print("点击登录按钮...")
        
        # 等待按钮变为可点击状态
        await asyncio.sleep(1)
        
        # 尝试多种选择器方式查找登录按钮
        try:
            # 方法1：通过文本内容查找
            login_button = await page.wait_for_selector("button:has-text('Sign in')", state="visible", timeout=5000)
            if login_button:
                await login_button.click()
            else:
                # 方法2：尝试通过类型和属性查找
                login_button = await page.wait_for_selector("button[type='submit']", state="visible", timeout=5000)
                if login_button:
                    await login_button.click()
                else:
                    # 方法3：使用更通用的方法，查找表单内的提交按钮
                    await page.evaluate("""
                        document.querySelector('form button[type="submit"]')?.click();
                    """)
        except Exception as e:
            print(f"使用常规方法点击登录按钮失败: {e}")
            # 方法4：使用JavaScript强制点击
            try:
                await page.evaluate("""
                    // 尝试多种方式找到登录按钮
                    let buttons = Array.from(document.querySelectorAll('button'));
                    let loginButton = buttons.find(button => 
                        button.textContent.includes('Sign in') || 
                        button.textContent.includes('登录') ||
                        button.type === 'submit'
                    );
                    
                    if (loginButton) {
                        loginButton.click();
                    } else {
                        // 如果找不到按钮，尝试提交表单
                        document.querySelector('form')?.submit();
                    }
                """)
            except Exception as e2:
                print(f"使用JavaScript点击登录按钮失败: {e2}")
        
        print("已尝试点击登录按钮")
        
        # 等待登录完成，页面加载 - 增加超时时间
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
            # 等待地图组件或主页元素出现
            await page.wait_for_selector(".map-container, #map, .mapContainer", state="visible", timeout=30000)
            print("登录成功")
        except Exception as e:
            print(f"等待登录完成超时: {e}")
            print("尝试继续执行后续操作...")
        
        await asyncio.sleep(10)
        # 输入坐标
        print(f"正在输入坐标: {latitude}, {longitude}")
        
        # 等待坐标输入框出现 - 使用更准确的选择器
        await page.wait_for_selector("input#searchInput[placeholder='TMC, Link, Lat-Long, or Place']", state="visible", timeout=10000)
        
        # 点击坐标输入框并输入坐标
        await page.click("input#searchInput[placeholder='TMC, Link, Lat-Long, or Place']")
        await page.fill("input#searchInput[placeholder='TMC, Link, Lat-Long, or Place']", f"{latitude}, {longitude}")
        
        # 按回车键提交坐标
        await page.press("input#searchInput[placeholder='TMC, Link, Lat-Long, or Place']", "Enter")
        
        # 等待地图上的标记出现，表示坐标已应用
        print("等待坐标在地图上显示...")
        # 添加一些等待时间，确保地图正确加载坐标
        await asyncio.sleep(30)
        
        # 点击Advanced按钮 - 使用更准确的选择器
        print("点击Advanced按钮")
        try:
            # 使用提供的精确选择器
            await page.wait_for_selector("div.debug-drawer-tab:has-text('Advanced')", state="visible", timeout=5000)
            await page.click("div.debug-drawer-tab:has-text('Advanced')")
        except Exception as e:
            print(f"使用精确选择器点击Advanced按钮失败: {e}")
            # 回退到其他方法
            try:
                # 尝试使用CSS类选择器
                await page.click("div.debug-drawer-tab")
            except Exception:
                # 再尝试使用文本内容
                await page.click("text=Advanced")
        
        # 等待Advanced面板加载
        await asyncio.sleep(1)
        
        # 点击Historical标签 - 使用更准确的选择器
        print("切换到Historical标签")
        try:
            # 使用提供的精确选择器
            await page.wait_for_selector("a[title='historicalTab']", state="visible", timeout=5000)
            await page.click("a[title='historicalTab']")
        except Exception as e:
            print(f"使用精确选择器点击Historical标签失败: {e}")
            # 回退到其他方法
            try:
                # 尝试使用包含span的选择器
                await page.click("a:has(span:text('Historical'))")
            except Exception:
                # 最后尝试使用文本内容
                await page.click("text=Historical")
        
        # 等待Historical面板加载
        await asyncio.sleep(1)
        
        # 输入UTC时间
        print(f"输入UTC时间: {utc_time}")
        
        # 等待时间输入框出现 - 使用更准确的选择器
        try:
            # 使用提供的精确ID选择器
            await page.wait_for_selector("input#historicalTab-datetimepicker", state="visible", timeout=5000)
            
            # 点击并清空输入框
            await page.click("input#historicalTab-datetimepicker")
            await page.fill("input#historicalTab-datetimepicker", utc_time)
            
            print("成功在时间输入框中输入UTC时间")
        except Exception as e:
            print(f"使用精确选择器访问时间输入框失败: {e}")
            # 回退到原来的方法
            try:
                await page.wait_for_selector("input[placeholder='Select date and time in UTC.']", state="visible")
                await page.click("input[placeholder='Select date and time in UTC.']")
                await page.fill("input[placeholder='Select date and time in UTC.']", utc_time)
            except Exception:
                # 最后尝试原始选择器
                await page.wait_for_selector("input[placeholder='YYYY-MM-DD HH:MM:SS']", state="visible")
                await page.click("input[placeholder='YYYY-MM-DD HH:MM:SS']")
                await page.fill("input[placeholder='YYYY-MM-DD HH:MM:SS']", utc_time)
        
        # 点击搜索按钮 - 使用更准确的选择器
        print("点击搜索按钮")
        try:
            # 使用提供的精确ID选择器
            await page.wait_for_selector("button#historicalTab-search", state="visible", timeout=5000)
            await page.click("button#historicalTab-search")
            print("成功点击搜索按钮")
        except Exception as e:
            print(f"使用精确选择器点击搜索按钮失败: {e}")
            # 回退到其他方法
            try:
                # 尝试使用文本内容
                await page.click("button:has-text('Search')")
            except Exception:
                # 最后尝试原始选择器
                await page.click("button:right-of(input[placeholder='YYYY-MM-DD HH:MM:SS'])")
        
        # 等待页面加载新时间数据
        print("等待页面加载新时间数据...")
        await asyncio.sleep(5)
        
        # 检查右上角时间是否变为用户输入的时间
        print("检查数据时间戳是否更新...")
        try:
            # 等待网络请求完成
            await page.wait_for_load_state("networkidle", timeout=0)
            
            # 等待时间戳控件可见
            await page.wait_for_selector("#timestamp-container #timestamp-label-avail", state="visible", timeout=10000)
            
            # 提取用户输入的日期部分和时间部分
            utc_datetime = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
            expected_day = utc_datetime.strftime("%d %b %Y")
            expected_time = utc_datetime.strftime("%H:%M")
            
            # 设置最大等待时间和重试间隔
            max_wait_time = 60  # 最多等待60秒
            retry_interval = 2  # 每2秒检查一次
            start_time = time.time()
            timestamp_matched = False
            
            print(f"期望的时间戳格式: 含有 {expected_day} {expected_time} UTC")
            
            # 循环检查时间戳是否匹配
            while (time.time() - start_time) < max_wait_time and not timestamp_matched:
                # 获取当前时间戳文本
                timestamp_text = await page.evaluate('document.querySelector("#timestamp-label-avail").textContent')
                print(f"当前时间戳: {timestamp_text}")
                
                # 检查时间戳是否包含预期的日期和时间
                if expected_day in timestamp_text and expected_time in timestamp_text:
                    print("✓ 时间戳已更新到指定的UTC时间")
                    timestamp_matched = True
                    break
                
                # 如果显示"Timestamp not available"，可能需要重新搜索
                not_avail_visible = await page.is_visible("#timestamp-label-not-avail")
                if not_avail_visible:
                    print("警告: 显示'Timestamp not available'，尝试重新搜索...")
                    try:
                        # 重新点击搜索按钮
                        await page.click("button#historicalTab-search")
                    except:
                        print("重新点击搜索按钮失败")
                
                # 等待一段时间后再次检查
                await asyncio.sleep(retry_interval)
            
            if not timestamp_matched:
                print("警告: 时间戳没有更新到预期值，但将继续截图")
        except Exception as e:
            print(f"检查时间戳时出错: {e}")
            print("将继续截图...")
        
        # 再等待一些时间确保地图完全加载
        await asyncio.sleep(10)


        print(f"截图保存到: {output_path}")
        await page.screenshot(path=output_path, full_page=True)
        
        await browser.close()
        print("操作完成")

def validate_datetime(datetime_str):
    """验证日期时间格式是否正确"""
    try:
        datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return datetime_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的日期时间格式: {datetime_str}，请使用YYYY-MM-DD HH:MM:SS格式")

def validate_coordinates(coord_str):
    """验证坐标格式是否正确"""
    try:
        return float(coord_str)
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的坐标值: {coord_str}，请使用数字")

def main():
    parser = argparse.ArgumentParser(description='获取HERE Traffic Viewer的指定坐标和时间的截图')
    parser.add_argument('--lat', type=validate_coordinates, required=True, help='纬度，如 40.7128')
    parser.add_argument('--lng', type=validate_coordinates, required=True, help='经度，如 -74.0060')
    parser.add_argument('--time', type=validate_datetime, required=True, help='UTC时间，格式为 YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--output', type=str, default='traffic_screenshot.png', help='截图保存路径')
    parser.add_argument('--visible', action='store_true', help='可视化模式，显示浏览器窗口')
    
    args = parser.parse_args()
    
    # 创建输出目录（如果需要）
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 运行异步函数
    asyncio.run(capture_traffic_screenshot(
        latitude=args.lat,
        longitude=args.lng,
        utc_time=args.time,
        output_path=args.output,
        headless=not args.visible
    ))

if __name__ == "__main__":
    main() 