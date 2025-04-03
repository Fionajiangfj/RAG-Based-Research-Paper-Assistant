import { Box, Text, VStack } from '@chakra-ui/react';
import { SourceNode } from '../types';

interface SourceCitationProps {
  node: SourceNode;
}

export const SourceCitation = ({ node }: SourceCitationProps) => {
  return (
    <Box p={4} borderWidth="1px" borderRadius="md" bg="gray.50">
      <VStack align="stretch" spacing={2}>
        <Text>{node.text}</Text>
        <Box display="flex" justifyContent="space-between" width="100%">
          <Box>
            {node.arxiv_url && (
              <Text fontSize="sm" color="gray.600">
                Source: <a href={`${node.arxiv_url}`} target="_blank" rel="noopener noreferrer" style={{ color: 'blue', textDecoration: 'underline' }}>
                  arXiv:{node.arxiv_url}
                </a>
              </Text>
            )}
          </Box>
          <Box>
            {node.score && (
              <Text fontSize="sm" color="gray.600">
                Relevance Score: {node.score.toFixed(2)}
              </Text>
            )}
          </Box>
        </Box>
      </VStack>
    </Box>
  );
};
