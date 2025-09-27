import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, Space, Typography, message, Tabs } from 'antd';
import { SaveOutlined, ReloadOutlined, CopyOutlined } from '@ant-design/icons';
import { Modal } from '../common/Modal';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface SystemMessageModalProps {
  open: boolean;
  onCancel: () => void;
  onSave: (systemMessage: string) => void;
  currentSystemMessage?: string;
}

export const SystemMessageModal: React.FC<SystemMessageModalProps> = ({
  open,
  onCancel,
  onSave,
  currentSystemMessage = '',
}) => {
  const [form] = Form.useForm();
  const [activeTemplate, setActiveTemplate] = useState<string>('');
  const [customMessage, setCustomMessage] = useState(currentSystemMessage);

  useEffect(() => {
    if (open) {
      setCustomMessage(currentSystemMessage);
      form.setFieldValue('systemMessage', currentSystemMessage);
    }
  }, [open, currentSystemMessage, form]);

  const systemTemplates = [
    {
      name: 'Default Assistant',
      value: 'default',
      description: 'General-purpose AI assistant',
      message: 'You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions.',
    },
    {
      name: 'Code Expert',
      value: 'coding',
      description: 'Specialized in programming and software development',
      message: 'You are an expert software developer and code reviewer. Analyze code thoroughly, suggest improvements, identify bugs, and provide best practices. Always explain your reasoning and include code examples when helpful.',
    },
    {
      name: 'Documentation Writer',
      value: 'documentation',
      description: 'Focused on creating clear documentation',
      message: 'You are a technical documentation specialist. Create clear, comprehensive documentation that is easy to understand. Include examples, use cases, and step-by-step instructions. Structure information logically and use appropriate formatting.',
    },
    {
      name: 'Code Reviewer',
      value: 'reviewer',
      description: 'Thorough code review and quality analysis',
      message: 'You are a senior code reviewer. Analyze code for:\n\n1. **Functionality** - Does it work correctly?\n2. **Security** - Are there vulnerabilities?\n3. **Performance** - Can it be optimized?\n4. **Maintainability** - Is it clean and readable?\n5. **Best Practices** - Follow coding standards?\n\nProvide specific, actionable feedback with examples.',
    },
    {
      name: 'Debugging Assistant',
      value: 'debugging',
      description: 'Help identify and fix bugs',
      message: 'You are a debugging expert. Help identify bugs by:\n\n1. Analyzing error messages and stack traces\n2. Examining code logic and flow\n3. Suggesting debugging techniques\n4. Providing step-by-step troubleshooting\n5. Offering preventive measures\n\nAlways ask clarifying questions when needed.',
    },
    {
      name: 'Architecture Advisor',
      value: 'architecture',
      description: 'Software architecture and design guidance',
      message: 'You are a software architecture expert. Provide guidance on:\n\n1. **System Design** - Scalable and maintainable architectures\n2. **Design Patterns** - Appropriate pattern selection\n3. **Technology Choices** - Framework and tool recommendations\n4. **Performance** - Optimization strategies\n5. **Security** - Secure design principles\n\nConsider trade-offs and provide multiple options when applicable.',
    },
    {
      name: 'Refactoring Specialist',
      value: 'refactoring',
      description: 'Code improvement and modernization',
      message: 'You are a refactoring specialist. Help improve code by:\n\n1. **Code Quality** - Remove code smells and technical debt\n2. **Readability** - Make code more understandable\n3. **Performance** - Optimize bottlenecks\n4. **Modularity** - Improve code organization\n5. **Modern Practices** - Update to current standards\n\nShow before and after examples with explanations.',
    },
  ];

  const handleTemplateChange = (templateValue: string) => {
    const template = systemTemplates.find(t => t.value === templateValue);
    if (template) {
      setActiveTemplate(templateValue);
      setCustomMessage(template.message);
      form.setFieldValue('systemMessage', template.message);
    }
  };

  const handleSave = () => {
    const message = customMessage.trim();
    if (message) {
      onSave(message);
      onCancel();
    } else {
      message.warning('Please enter a system message');
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      message.success('Copied to clipboard');
    } catch (error) {
      message.error('Failed to copy');
    }
  };

  const handleReset = () => {
    const defaultTemplate = systemTemplates[0];
    setActiveTemplate(defaultTemplate.value);
    setCustomMessage(defaultTemplate.message);
    form.setFieldValue('systemMessage', defaultTemplate.message);
  };

  return (
    <Modal
      title="System Message Configuration"
      open={open}
      onCancel={onCancel}
      onOk={handleSave}
      width={800}
      okText="Save System Message"
      cancelText="Cancel"
    >
      <Tabs defaultActiveKey="templates">
        <TabPane tab="Templates" key="templates">
          <div className="space-y-4">
            <div>
              <Text className="block mb-2 font-medium">Choose a Template:</Text>
              <Select
                value={activeTemplate}
                onChange={handleTemplateChange}
                placeholder="Select a system message template"
                className="w-full"
              >
                {systemTemplates.map(template => (
                  <Option key={template.value} value={template.value}>
                    <div>
                      <div className="font-medium">{template.name}</div>
                      <div className="text-xs text-gray-500">{template.description}</div>
                    </div>
                  </Option>
                ))}
              </Select>
            </div>

            {activeTemplate && (
              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Text strong>Preview:</Text>
                  <Button
                    type="link"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopy(customMessage)}
                  >
                    Copy
                  </Button>
                </div>
                <div className="text-sm whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {customMessage}
                </div>
              </div>
            )}
          </div>
        </TabPane>

        <TabPane tab="Custom" key="custom">
          <Form form={form} layout="vertical">
            <Form.Item
              label="System Message"
              name="systemMessage"
              help="This message defines how the AI assistant should behave and respond."
            >
              <TextArea
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={12}
                placeholder="Enter a custom system message..."
                className="font-mono text-sm"
              />
            </Form.Item>

            <div className="flex justify-between items-center">
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleReset}
                >
                  Reset to Default
                </Button>
                <Text type="secondary" className="text-sm">
                  Characters: {customMessage.length}
                </Text>
              </Space>

              <Button
                type="link"
                icon={<CopyOutlined />}
                onClick={() => handleCopy(customMessage)}
              >
                Copy Message
              </Button>
            </div>
          </Form>
        </TabPane>

        <TabPane tab="Examples" key="examples">
          <div className="space-y-4">
            <Title level={5}>System Message Examples</Title>
            
            {systemTemplates.slice(1).map((template, index) => (
              <div key={template.value} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <Text strong>{template.name}</Text>
                    <Text type="secondary" className="block text-sm">{template.description}</Text>
                  </div>
                  <Space>
                    <Button
                      size="small"
                      onClick={() => {
                        setCustomMessage(template.message);
                        form.setFieldValue('systemMessage', template.message);
                      }}
                    >
                      Use This
                    </Button>
                    <Button
                      type="link"
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => handleCopy(template.message)}
                    />
                  </Space>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded max-h-32 overflow-y-auto whitespace-pre-wrap">
                  {template.message}
                </div>
              </div>
            ))}
          </div>
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default SystemMessageModal;