"""Enhanced debugging utilities."""
import json
import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from functools import wraps
import time


class DebugLogger:
    """Enhanced logger for debugging."""
    
    def __init__(self, config: Dict[str, Any], verbose: bool = False):
        self.config = config. get('debug', {})
        self. verbose = verbose or self.config.get('enabled', False)
        self.stage_timings = {}
        self.stage_count = 0
        self.start_time = datetime.utcnow()
        
        # Setup logging
        self._setup_logging()
        
        # Create debug directories
        if self.config.get('save_intermediate', {}).get('enabled'):
            Path(self.config['save_intermediate']['path']).mkdir(parents=True, exist_ok=True)
        
        if self. config.get('outputs', {}).get('file'):
            Path(self.config['outputs']['file_path']).parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config. get('level', 'INFO'))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler. setFormatter(console_format)
        
        # File handler
        handlers = [console_handler]
        if self.config.get('outputs', {}).get('file'):
            file_handler = logging.FileHandler(
                self.config['outputs']['file_path'],
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(console_format)
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=handlers,
            force=True
        )
        
        self.logger = logging.getLogger('DebugLogger')
    
    def stage_start(self, stage_name: str):
        """Mark stage start."""
        self.stage_count += 1
        self. stage_timings[stage_name] = {'start': time.time()}
        
        if not self.verbose:
            return
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print(f"▶️  STAGE {self.stage_count}: {stage_name} [START]")
        print(f"⏱️  Total Elapsed: {elapsed:.2f}s")
        print(f"{'='*80}")
        
        self.logger.info(f"Stage {self.stage_count} START: {stage_name}")
    
    def stage_end(self, stage_name: str, status: str = "SUCCESS"):
        """Mark stage end."""
        if stage_name in self.stage_timings:
            self.stage_timings[stage_name]['end'] = time.time()
            self.stage_timings[stage_name]['duration'] = (
                self.stage_timings[stage_name]['end'] - 
                self. stage_timings[stage_name]['start']
            )
        
        if not self.verbose:
            return
        
        duration = self.stage_timings. get(stage_name, {}). get('duration', 0)
        elapsed = (datetime.utcnow() - self.start_time). total_seconds()
        
        symbols = {
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        
        symbol = symbols.get(status, "•")
        
        print(f"\n{'='*80}")
        print(f"{symbol} STAGE {self.stage_count}: {stage_name} [{status}]")
        print(f"⏱️  Stage Duration: {duration:.2f}s")
        print(f"⏱️  Total Elapsed: {elapsed:.2f}s")
        print(f"{'='*80}")
        
        self.logger.info(f"Stage {self.stage_count} {status}: {stage_name} (Duration: {duration:.2f}s)")
    
    def log_state(self, stage_name: str, state: Dict[str, Any]):
        """Log current state."""
        if not self.config.get('log_state'):
            return
        
        self.logger.debug(f"State after {stage_name}:")
        
        # Log key state values (exclude large data)
        state_summary = {
            k: v for k, v in state.items() 
            if k not in ['test_results', 'failure_details', 'collected_data', 'final_report']
            and v is not None
        }
        
        for key, value in state_summary.items():
            if isinstance(value, (str, int, float, bool)):
                self.logger.debug(f"  {key}: {value}")
            elif isinstance(value, list):
                self.logger.debug(f"  {key}: [{len(value)} items]")
            elif isinstance(value, dict):
                self. logger.debug(f"  {key}: {{{len(value)} keys}}")
        
        # Save to file if enabled
        if self.config. get('save_intermediate', {}). get('enabled'):
            self._save_intermediate(stage_name, 'state', state_summary)
    
    def log_data(self, title: str, data: Dict[str, Any]):
        """Log structured data."""
        if not self. verbose:
            return
        
        print(f"\n   📊 {title}:")
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                print(f"      • {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"      • {key}: {value}")
        
        self.logger.debug(f"{title}: {json.dumps(data, default=str, indent=2)}")
    
    def log_detail(self, key: str, value: Any):
        """Log a detail."""
        if not self.verbose:
            return
        
        print(f"   📌 {key}: {value}")
        self.logger.debug(f"{key}: {value}")
    
    def log_section(self, title: str):
        """Log a section header."""
        if not self.verbose:
            return
        
        print(f"\n   {'─'*70}")
        print(f"   📋 {title}")
        print(f"   {'─'*70}")
        
        self. logger.debug(f"=== {title} ===")
    
    def log_llm_prompt(self, prompt: str):
        """Log LLM prompt."""
        if not self.config.get('log_llm_prompts'):
            return
        
        self.logger.info("LLM Prompt:")
        self.logger.info(f"\n{prompt}\n")
        
        if self.verbose:
            print(f"\n   🤖 LLM PROMPT:")
            print(f"   {'┌'+'─'*68+'┐'}")
            lines = prompt.split('\n')
            for i, line in enumerate(lines):
                if i < 20:
                    print(f"   │ {line[:66]:<66} │")
                elif i == 20:
                    print(f"   │ {'...  (truncated, see debug log for full)':<66} │")
                    break
            print(f"   {'└'+'─'*68+'┘'}")
        
        # Save to file
        if self.config.get('save_intermediate', {}).get('enabled'):
            self._save_intermediate('llm', 'prompt', {'prompt': prompt})
    
    def log_llm_response(self, response: str):
        """Log LLM response."""
        if not self.config.get('log_llm_responses'):
            return
        
        self.logger.info("LLM Response:")
        self.logger. info(f"\n{response}\n")
        
        if self.verbose:
            print(f"\n   💬 LLM RESPONSE:")
            print(f"   {'┌'+'─'*68+'┐'}")
            lines = response.split('\n')
            for i, line in enumerate(lines):
                if i < 20:
                    print(f"   │ {line[:66]:<66} │")
                elif i == 20:
                    print(f"   │ {'... (truncated, see debug log for full)':<66} │")
                    break
            print(f"   {'└'+'─'*68+'┘'}")
        
        # Save to file
        if self.config. get('save_intermediate', {}). get('enabled'):
            self._save_intermediate('llm', 'response', {'response': response})
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with full traceback."""
        error_msg = str(error)
        error_trace = traceback.format_exc()
        
        self.logger.error(f"Error in {context}: {error_msg}")
        
        if self.config.get('log_errors_full'):
            self.logger.error(f"Full traceback:\n{error_trace}")
        
        if self.verbose:
            print(f"\n   ❌ ERROR in {context}")
            print(f"   Message: {error_msg}")
            if self.config.get('log_errors_full'):
                print(f"\n   Traceback:")
                print(f"   {error_trace}")
        
        # Save to file
        if self.config.get('save_intermediate', {}).get('enabled'):
            self._save_intermediate('errors', context, {
                'error': error_msg,
                'traceback': error_trace,
                'context': context
            })
    
    def log_test_output(self, output: str, exit_code: int):
        """Log test execution output."""
        if not self. config.get('log_test_output'):
            return
        
        self.logger.info(f"Test Execution Output (exit code: {exit_code}):")
        self.logger.info(f"\n{output}\n")
        
        if self.verbose:
            print(f"\n   🧪 TEST OUTPUT (Exit Code: {exit_code}):")
            print(f"   {'┌'+'─'*68+'┐'}")
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if i < 30:
                    print(f"   │ {line[:66]:<66} │")
                elif i == 30:
                    print(f"   │ {'... (truncated, see debug log for full)':<66} │")
                    break
            print(f"   {'└'+'─'*68+'┘'}")
        
        # Save to file
        if self.config.get('save_intermediate', {}).get('enabled'):
            self._save_intermediate('test_execution', 'output', {
                'output': output,
                'exit_code': exit_code
            })
    
    def _save_intermediate(self, category: str, name: str, data: Any):
        """Save intermediate data to file."""
        try:
            base_path = Path(self.config['save_intermediate']['path'])
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            # Create category directory
            category_path = base_path / category
            category_path.mkdir(parents=True, exist_ok=True)
            
            # Save as JSON
            if 'json' in self.config['save_intermediate']. get('formats', []):
                json_path = category_path / f"{name}_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            
            # Save as text
            if 'txt' in self.config['save_intermediate'].get('formats', []):
                txt_path = category_path / f"{name}_{timestamp}.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    if isinstance(data, dict):
                        for key, value in data. items():
                            f.write(f"{key}:\n{value}\n\n")
                    else:
                        f. write(str(data))
        
        except Exception as e:
            self.logger.warning(f"Failed to save intermediate data: {str(e)}")
    
    def summary(self):
        """Print execution summary."""
        total_elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print(f"📊 EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"   Total Time: {total_elapsed:.2f}s")
        print(f"   Stages: {self. stage_count}")
        print(f"\n   Stage Timings:")
        
        for stage, timing in self.stage_timings.items():
            duration = timing. get('duration', 0)
            percentage = (duration / total_elapsed * 100) if total_elapsed > 0 else 0
            print(f"      • {stage}: {duration:.2f}s ({percentage:.1f}%)")
        
        print(f"{'='*80}\n")
        
        self.logger.info(f"Execution complete. Total time: {total_elapsed:.2f}s")


def debug_stage(stage_name: str):
    """Decorator to add debugging to a stage function."""
    def decorator(func):
        @wraps(func)
        def wrapper(state, config):
            # Get or create debug logger
            debug_logger = state.get('_debug_logger')
            if not debug_logger:
                from . config import Config
                cfg = config if isinstance(config, Config) else Config()
                debug_logger = DebugLogger(cfg._config, state.get('verbose', False))
                state['_debug_logger'] = debug_logger
            
            # Start stage
            debug_logger.stage_start(stage_name)
            
            try:
                # Execute stage
                result = func(state, config)
                
                # Log state
                debug_logger.log_state(stage_name, {**state, **result})
                
                # End stage
                debug_logger.stage_end(stage_name, "SUCCESS")
                
                return result
            
            except Exception as e:
                # Log error
                debug_logger.log_error(e, stage_name)
                debug_logger.stage_end(stage_name, "ERROR")
                raise
        
        return wrapper
    return decorator