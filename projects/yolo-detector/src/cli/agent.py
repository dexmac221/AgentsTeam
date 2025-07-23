#!/usr/bin/env python3
"""
CLI Agent Interface for YOLO Object Detector
Optimized for AI agent interaction and automation
"""

import asyncio
import json
import argparse
import sys
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import httpx
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
import yaml

from ..config.settings import settings, get_cli_config, update_settings, get_model_info

console = Console()


class YOLODetectorAgent:
    """CLI Agent for YOLO Object Detector"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.is_monitoring = False
        self.last_detection_count = 0
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        try:
            response = await self.client.get(f"{self.base_url}/cli/status")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def quick_detect(self) -> Dict[str, Any]:
        """Get quick detection results"""
        try:
            response = await self.client.get(f"{self.base_url}/cli/quick-detect")
            return response.json()
        except Exception as e:
            return {"error": str(e), "count": 0, "objects": []}
    
    async def get_full_detection(self) -> Dict[str, Any]:
        """Get full detection results with all metadata"""
        try:
            response = await self.client.post(f"{self.base_url}/detect")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            response = await self.client.get(f"{self.base_url}/stats")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        try:
            response = await self.client.get(f"{self.base_url}/config")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration"""
        try:
            response = await self.client.post(f"{self.base_url}/config", json=config)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def monitor_continuous(self, duration: int = 60, interval: float = 1.0):
        """Monitor detections continuously"""
        self.is_monitoring = True
        start_time = time.time()
        detection_history = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Monitoring detections...", total=duration)
            
            while self.is_monitoring and (time.time() - start_time) < duration:
                try:
                    # Get detection results
                    result = await self.quick_detect()
                    
                    if "error" not in result:
                        detection_history.append({
                            "timestamp": time.time(),
                            "count": result["count"],
                            "fps": result["fps"],
                            "objects": result["objects"]
                        })
                        
                        # Update progress description
                        progress.update(
                            task,
                            completed=(time.time() - start_time),
                            description=f"Objects: {result['count']} | FPS: {result['fps']} | Total detections: {len(detection_history)}"
                        )
                        
                        # Notify on significant changes
                        if abs(result["count"] - self.last_detection_count) >= 3:
                            console.print(f"[yellow]Detection change: {self.last_detection_count} → {result['count']} objects[/yellow]")
                            self.last_detection_count = result["count"]
                    
                    await asyncio.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.is_monitoring = False
                    break
                except Exception as e:
                    console.print(f"[red]Monitor error: {e}[/red]")
                    await asyncio.sleep(interval)
        
        return detection_history


# CLI Commands
@click.group()
@click.option('--url', default='http://localhost:8000', help='YOLO detector service URL')
@click.option('--format', 'output_format', default='table', type=click.Choice(['json', 'yaml', 'table']), help='Output format')
@click.pass_context
def cli(ctx, url, output_format):
    """YOLO Object Detector CLI Agent"""
    ctx.ensure_object(dict)
    ctx.obj['url'] = url
    ctx.obj['format'] = output_format


@cli.command()
@click.pass_context
async def health(ctx):
    """Check system health"""
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        result = await agent.health_check()
        output_result(result, ctx.obj['format'])


@cli.command()
@click.pass_context
async def status(ctx):
    """Get system status"""
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        result = await agent.get_status()
        output_result(result, ctx.obj['format'])


@cli.command()
@click.option('--full', is_flag=True, help='Get full detection details')
@click.pass_context
async def detect(ctx, full):
    """Get current detection results"""
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        if full:
            result = await agent.get_full_detection()
        else:
            result = await agent.quick_detect()
        output_result(result, ctx.obj['format'])


@cli.command()
@click.pass_context
async def stats(ctx):
    """Get system statistics"""
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        result = await agent.get_stats()
        output_result(result, ctx.obj['format'])


@cli.command()
@click.pass_context
async def config(ctx):
    """Get current configuration"""
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        result = await agent.get_config()
        output_result(result, ctx.obj['format'])


@cli.command()
@click.option('--confidence', type=float, help='Detection confidence threshold (0.1-1.0)')
@click.option('--iou', type=float, help='IoU threshold (0.1-1.0)')
@click.option('--tracking/--no-tracking', help='Enable/disable tracking')
@click.option('--segmentation/--no-segmentation', help='Enable/disable segmentation')
@click.option('--model', help='Model size (yolov8n.pt, yolov8s.pt, etc.)')
@click.option('--camera-url', help='Camera stream URL')
@click.pass_context
async def configure(ctx, confidence, iou, tracking, segmentation, model, camera_url):
    """Update configuration"""
    config_updates = {}
    
    if confidence is not None:
        config_updates['detection_confidence'] = confidence
    if iou is not None:
        config_updates['iou_threshold'] = iou
    if tracking is not None:
        config_updates['enable_tracking'] = tracking
    if segmentation is not None:
        config_updates['enable_segmentation'] = segmentation
    if model:
        config_updates['model_size'] = model
    if camera_url:
        config_updates['camera_url'] = camera_url
    
    if not config_updates:
        console.print("[yellow]No configuration changes specified[/yellow]")
        return
    
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        result = await agent.update_config(config_updates)
        output_result(result, ctx.obj['format'])


@cli.command()
@click.option('--duration', default=60, help='Monitoring duration in seconds')
@click.option('--interval', default=1.0, help='Update interval in seconds')
@click.option('--threshold', default=0.5, help='Detection confidence threshold')
@click.option('--classes', help='Comma-separated list of classes to monitor')
@click.pass_context
async def monitor(ctx, duration, interval, threshold, classes):
    """Monitor detections continuously"""
    console.print(f"[green]Starting detection monitoring for {duration} seconds...[/green]")
    
    # Update configuration if needed
    config_updates = {'detection_confidence': threshold}
    
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        # Apply threshold
        await agent.update_config(config_updates)
        
        # Start monitoring
        history = await agent.monitor_continuous(duration, interval)
        
        # Summarize results
        if history:
            total_detections = sum(h['count'] for h in history)
            avg_fps = sum(h['fps'] for h in history) / len(history)
            
            summary = {
                "monitoring_duration": duration,
                "total_frames": len(history),
                "total_detections": total_detections,
                "average_fps": round(avg_fps, 1),
                "detection_rate": round(total_detections / len(history), 1),
                "peak_objects": max(h['count'] for h in history),
                "min_objects": min(h['count'] for h in history)
            }
            
            console.print("\n[bold]Monitoring Summary:[/bold]")
            output_result(summary, ctx.obj['format'])


@cli.command()
@click.option('--watch', is_flag=True, help='Watch for changes continuously')
@click.pass_context
async def live(ctx, watch):
    """Live detection dashboard"""
    async with YOLODetectorAgent(ctx.obj['url']) as agent:
        if watch:
            await live_dashboard(agent)
        else:
            # Single snapshot
            status = await agent.get_status()
            detection = await agent.quick_detect()
            stats = await agent.get_stats()
            
            display_live_dashboard(status, detection, stats)


async def live_dashboard(agent: YOLODetectorAgent):
    """Live updating dashboard"""
    
    def make_layout() -> Layout:
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        return layout
    
    layout = make_layout()
    
    async def update_display():
        while True:
            try:
                # Get fresh data
                status = await agent.get_status()
                detection = await agent.quick_detect()
                stats_data = await agent.get_stats()
                
                # Update layout
                layout["header"].update(
                    Panel(
                        f"YOLO Object Detector - Live Dashboard | {time.strftime('%H:%M:%S')}",
                        style="bold blue"
                    )
                )
                
                # System status
                status_table = Table(title="System Status")
                status_table.add_column("Component", style="cyan")
                status_table.add_column("Status", justify="center")
                
                status_table.add_row("Camera", "🟢 Connected" if status.get('camera_connected') else "🔴 Disconnected")
                status_table.add_row("Detector", "🟢 Ready" if status.get('detector_ready') else "🟡 Loading")
                status_table.add_row("FPS", f"{status.get('current_fps', 0):.1f}")
                
                layout["left"].update(Panel(status_table))
                
                # Current detections
                det_table = Table(title="Current Detections")
                det_table.add_column("Class", style="green")
                det_table.add_column("Confidence", justify="center")
                det_table.add_column("Track ID", justify="center")
                
                for obj in detection.get('objects', [])[:10]:
                    det_table.add_row(
                        obj['class'],
                        f"{obj['confidence']:.2f}",
                        str(obj.get('track_id', '-'))
                    )
                
                layout["right"].update(Panel(det_table))
                
                layout["footer"].update(
                    Panel(
                        f"Objects: {detection.get('count', 0)} | FPS: {detection.get('fps', 0):.1f} | Press Ctrl+C to exit",
                        style="dim"
                    )
                )
                
                await asyncio.sleep(1.0)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                layout["footer"].update(Panel(f"Error: {e}", style="red"))
                await asyncio.sleep(1.0)
    
    with Live(layout, refresh_per_second=1, screen=True):
        await update_display()


def display_live_dashboard(status: Dict, detection: Dict, stats: Dict):
    """Display single snapshot dashboard"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
    )
    
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    # Header
    layout["header"].update(
        Panel("YOLO Object Detector - Status Snapshot", style="bold blue")
    )
    
    # System info
    sys_table = Table(title="System Status")
    sys_table.add_column("Metric", style="cyan")
    sys_table.add_column("Value", justify="right")
    
    sys_table.add_row("Camera Connected", "✓" if status.get('camera_connected') else "✗")
    sys_table.add_row("Detector Ready", "✓" if status.get('detector_ready') else "✗")
    sys_table.add_row("Current FPS", f"{status.get('current_fps', 0):.1f}")
    sys_table.add_row("Detection Count", str(status.get('detection_count', 0)))
    
    layout["left"].update(Panel(sys_table))
    
    # Recent detections
    det_table = Table(title="Recent Detections")
    det_table.add_column("Class", style="green")
    det_table.add_column("Confidence", justify="center")
    det_table.add_column("Track ID", justify="center")
    
    for obj in detection.get('objects', []):
        det_table.add_row(
            obj['class'],
            f"{obj['confidence']:.2f}",
            str(obj.get('track_id', '-'))
        )
    
    layout["right"].update(Panel(det_table))
    
    console.print(layout)


def output_result(result: Any, format_type: str = 'table'):
    """Output result in specified format"""
    if format_type == 'json':
        console.print_json(data=result)
    elif format_type == 'yaml':
        console.print(Syntax(yaml.dump(result, default_flow_style=False), "yaml"))
    else:
        # Table format
        if isinstance(result, dict):
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            
            def add_rows(data, prefix=""):
                for key, value in data.items():
                    full_key = f"{prefix}{key}" if prefix else key
                    if isinstance(value, dict):
                        add_rows(value, f"{full_key}.")
                    else:
                        table.add_row(full_key, str(value))
            
            add_rows(result)
            console.print(table)
        else:
            console.print(result)


def main():
    """Main entry point"""
    # Convert sync click to async
    import asyncio
    
    def run_async(coro):
        return asyncio.run(coro)
    
    # Patch click commands to be async
    for name, cmd in cli.commands.items():
        if asyncio.iscoroutinefunction(cmd.callback):
            original_callback = cmd.callback
            cmd.callback = lambda *args, **kwargs: run_async(original_callback(*args, **kwargs))
    
    cli()


if __name__ == "__main__":
    main()