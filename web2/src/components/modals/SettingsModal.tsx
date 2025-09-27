import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Slider, Switch, Button, Tabs, Typography, message } from 'antd';
import { Modal } from '../common/Modal';
import type { AppSettings } from '../../types';
import { useTheme } from '../../themes';
import ApiService from '../../services/api';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface SettingsModalProps {
  open: boolean;
  onCancel: () => void;
  onSave: (settings: AppSettings) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  open,
  onCancel,
  onSave,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    if (open) {
      loadSettings();
    }
  }, [open]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await ApiService.getSettings();
      if (response.success && response.data) {
        form.setFieldsValue(response.data);
      } else {
        message.error(response.error || 'Failed to load settings');
      }
    } catch (error) {
      message.error('Error loading settings');
      console.error('Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const values = await form.validateFields();
      
      const response = await ApiService.updateSettings(values);
      if (response.success && response.data) {
        onSave(response.data);
        message.success('Settings saved successfully');
        onCancel();
      } else {
        message.error(response.error || 'Failed to save settings');
      }
    } catch (error: any) {
      if (error.errorFields) {
        message.error('Please correct the validation errors');
      } else {
        message.error('Error saving settings');
        console.error('Error saving settings:', error);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleThemeChange = (newTheme: 'light' | 'dark') => {
    setTheme(newTheme);
    form.setFieldValue('theme', newTheme);
  };

  const providerOptions = [
    { label: 'OpenRouter', value: 'openrouter' },
    { label: 'OpenAI', value: 'openai' },
    { label: 'Anthropic', value: 'anthropic' },
    { label: 'Google', value: 'google' },
    { label: 'Local', value: 'local' },
  ];

  const modelOptions = [
    'x-ai/grok-code-fast-1',
    'anthropic/claude-3-sonnet',
    'openai/gpt-4-turbo',
    'google/gemini-pro',
    'meta/llama-2-70b',
    'mistral/mistral-large',
  ];

  return (
    <Modal
      title="Settings"
      open={open}
      onCancel={onCancel}
      onOk={handleSave}
      width={720}
      confirmLoading={saving}
      okText="Save Settings"
      cancelText="Cancel"
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          theme: theme,
          provider: 'openrouter',
          model: 'x-ai/grok-code-fast-1',
          maxTokens: 4000,
          temperature: 0.7,
          systemPrompt: 'You are a helpful AI assistant specialized in code analysis and development.',
        }}
      >
        <Tabs defaultActiveKey="general">
          <TabPane tab="General" key="general">
            <div className="space-y-4">
              <Form.Item
                label="Theme"
                name="theme"
                tooltip="Choose between light and dark theme"
              >
                <Select onChange={handleThemeChange}>
                  <Option value="light">Light</Option>
                  <Option value="dark">Dark</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="Language"
                tooltip="Interface language"
              >
                <Select defaultValue="en">
                  <Option value="en">English</Option>
                  <Option value="es">Spanish</Option>
                  <Option value="fr">French</Option>
                  <Option value="de">German</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="Auto-save conversations"
                tooltip="Automatically save conversations"
              >
                <Switch defaultChecked />
              </Form.Item>

              <Form.Item
                label="Show line numbers in code"
                tooltip="Display line numbers in code blocks"
              >
                <Switch defaultChecked />
              </Form.Item>
            </div>
          </TabPane>

          <TabPane tab="AI Provider" key="provider">
            <div className="space-y-4">
              <Form.Item
                label="Provider"
                name="provider"
                rules={[{ required: true, message: 'Please select a provider' }]}
                tooltip="AI service provider"
              >
                <Select>
                  {providerOptions.map(provider => (
                    <Option key={provider.value} value={provider.value}>
                      {provider.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                label="Model"
                name="model"
                rules={[{ required: true, message: 'Please select a model' }]}
                tooltip="AI model to use for responses"
              >
                <Select>
                  {modelOptions.map(model => (
                    <Option key={model} value={model}>{model}</Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                label="API Key"
                tooltip="Your API key for the selected provider"
              >
                <Input.Password placeholder="Enter your API key" />
              </Form.Item>

              <Form.Item
                label="Base URL"
                tooltip="Custom API base URL (optional)"
              >
                <Input placeholder="https://api.example.com" />
              </Form.Item>
            </div>
          </TabPane>

          <TabPane tab="Model Parameters" key="parameters">
            <div className="space-y-6">
              <Form.Item
                label="Max Tokens"
                name="maxTokens"
                tooltip="Maximum number of tokens in the response"
              >
                <Slider
                  min={100}
                  max={8000}
                  step={100}
                  marks={{
                    100: '100',
                    2000: '2K',
                    4000: '4K',
                    8000: '8K',
                  }}
                />
              </Form.Item>

              <Form.Item
                label="Temperature"
                name="temperature"
                tooltip="Controls randomness in responses (0 = deterministic, 1 = creative)"
              >
                <Slider
                  min={0}
                  max={1}
                  step={0.1}
                  marks={{
                    0: '0',
                    0.5: '0.5',
                    1: '1',
                  }}
                />
              </Form.Item>

              <Form.Item
                label="System Prompt"
                name="systemPrompt"
                tooltip="Default system message for AI behavior"
              >
                <TextArea
                  rows={4}
                  placeholder="Enter system prompt..."
                />
              </Form.Item>

              <Form.Item
                label="Enable streaming"
                tooltip="Stream responses as they're generated"
              >
                <Switch defaultChecked />
              </Form.Item>
            </div>
          </TabPane>

          <TabPane tab="Advanced" key="advanced">
            <div className="space-y-4">
              <Title level={5}>Performance</Title>
              
              <Form.Item
                label="Request timeout (seconds)"
                tooltip="How long to wait for AI responses"
              >
                <Slider
                  min={5}
                  max={120}
                  step={5}
                  defaultValue={30}
                  marks={{
                    5: '5s',
                    30: '30s',
                    60: '1m',
                    120: '2m',
                  }}
                />
              </Form.Item>

              <Form.Item
                label="Retry attempts"
                tooltip="Number of retry attempts for failed requests"
              >
                <Select defaultValue="3">
                  <Option value="1">1</Option>
                  <Option value="2">2</Option>
                  <Option value="3">3</Option>
                  <Option value="5">5</Option>
                </Select>
              </Form.Item>

              <Title level={5}>Debug</Title>

              <Form.Item
                label="Enable debug logging"
                tooltip="Log detailed information for troubleshooting"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="Show token usage"
                tooltip="Display token consumption information"
              >
                <Switch defaultChecked />
              </Form.Item>
            </div>
          </TabPane>
        </Tabs>
      </Form>
    </Modal>
  );
};

export default SettingsModal;